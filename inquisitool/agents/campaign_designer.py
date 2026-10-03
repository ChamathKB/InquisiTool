import json
from datetime import datetime, timezone

from crewai import LLM, Agent, Crew, Process, Task

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.4,
    api_key=GEMINI_API_KEY,
)

campaign_designer = Agent(
    role="Campaign Design Assistant",
    goal="Help users design effective survey campaigns through a short conversational flow",
    backstory="""You are an expert survey strategist. You gather information about a user's
        research goal through focused clarifying questions, then produce a complete, well-structured
        campaign configuration. You ask one question at a time and never overwhelm the user.""",
    llm=llm,
    verbose=True,
)

_SYSTEM = """You are helping a user design a survey campaign. Your job is to gather enough
information through a short conversation (2-3 turns max) then produce a complete campaign config.

Rules:
- Ask ONE clarifying question per turn if you need more information.
- Once you have: goal, target audience, rough duration, and desired depth — output the config.
- Never ask more than 3 clarifying questions total before producing the config.
- When ready to produce the config, respond with EXACTLY this format (no extra text):
  COMPLETE: <json>
  where <json> is a valid JSON object with these keys:
    campaign_name        (string)
    campaign_description (string)
    target_audience      (string)
    number_of_questions  (integer, 3-10)
    branch_delta         (integer, 1-3)
    status               (always "active")
    start_date           (ISO datetime string, today)
    end_date             (ISO datetime string, 30 days from today unless user specified)
- If still gathering info, respond with just a single conversational question (no COMPLETE prefix).
"""


def _format_history(history: list) -> str:
    if not history:
        return ""
    return "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history)


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _in_30_days_iso() -> str:
    from datetime import timedelta

    return (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")


def chat_design(message: str, history: list = []) -> tuple[str, bool, dict | None]:
    """
    Returns (reply, is_complete, config_dict | None).
    config_dict maps directly to CampaignCreate fields (minus collection_id).
    """
    history_text = _format_history(history)
    turn_count = len([m for m in history if m.get("role") == "user"]) + 1

    task = Task(
        description=f"""{_SYSTEM}

Today's date (UTC): {_today_iso()}
Default end date (30 days out): {_in_30_days_iso()}

Conversation so far:
{history_text if history_text else "(none — this is the first message)"}

User: {message}

This is turn {turn_count} of the conversation.
{"You MUST produce the COMPLETE config now — do not ask any more questions." if turn_count >= 3 else ""}
""",
        expected_output=("Either a single clarifying question, or COMPLETE: followed by a JSON config object."),
        agent=campaign_designer,
    )

    crew = Crew(agents=[campaign_designer], tasks=[task], process=Process.sequential, verbose=True)
    raw = crew.kickoff().raw.strip()

    if raw.startswith("COMPLETE:"):
        json_str = raw[len("COMPLETE:") :].strip()
        # strip markdown code fences if present
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            json_str = json_str.strip()
        config = json.loads(json_str)
        summary = (
            f"Here's your campaign config — **{config.get('campaign_name')}**. "
            "I've pre-filled the form below. Select a knowledge base collection and adjust any fields, then hit Create."
        )
        return summary, True, config

    return raw, False, None

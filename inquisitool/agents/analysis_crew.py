import json

from crewai import LLM, Agent, Crew, Process, Task

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.3,
    api_key=GEMINI_API_KEY,
)

summarizer = Agent(
    role="Response Summarizer",
    goal="Summarize survey responses per question concisely",
    backstory="You are an expert at distilling large volumes of survey answers into clear, concise summaries.",
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="Theme and Sentiment Analyst",
    goal="Identify recurring themes and overall sentiment from survey summaries",
    backstory="You are a qualitative research analyst skilled at finding patterns and sentiment in survey data.",
    llm=llm,
    verbose=True,
)

insight_generator = Agent(
    role="Insight Generator",
    goal="Produce actionable recommendations from the analysis",
    backstory="You are a strategic consultant who turns research findings into clear, actionable business insights.",
    llm=llm,
    verbose=True,
)


def _format_interactions(interactions: list) -> str:
    lines = []
    for i, interaction in enumerate(interactions, 1):
        questions = interaction.get("questions", [])
        answers = interaction.get("answers", [])
        lines.append(f"--- Respondent {i} ---")
        for q, a in zip(questions, answers):
            lines.append(f"Q: {q}")
            lines.append(f"A: {a or '(no answer)'}")
    return "\n".join(lines)


def analyze_campaign(campaign: dict, interactions: list) -> dict:
    name = campaign.get("campaign_name", "")
    description = campaign.get("campaign_description", "")
    formatted = _format_interactions(interactions)
    total = len(interactions)

    summarize_task = Task(
        description=f"""You are analyzing survey responses for campaign "{name}" ({description}).
        There are {total} completed responses.

        Raw Q&A data:
        {formatted}

        For each unique question asked across all respondents, write a 1-2 sentence summary of what respondents said.
        Return a JSON array of objects with keys "question" and "summary".""",
        expected_output='A JSON array like: [{"question": "...", "summary": "..."}]',
        agent=summarizer,
    )

    analysis_task = Task(
        description="""Using the question summaries from the previous task, identify:
        1. The top recurring themes (as a list of short phrases)
        2. The overall sentiment: one of "positive", "neutral", or "negative"

        Return a JSON object with keys "themes" (array of strings) and "sentiment" (string).""",
        expected_output='A JSON object like: {"themes": ["...", "..."], "sentiment": "positive"}',
        agent=analyst,
        context=[summarize_task],
    )

    insights_task = Task(
        description="""Based on the summaries and analysis from the previous tasks, generate 3-5 concise,
        actionable insights or recommendations for the campaign owner.

        Return a JSON array of strings, each being one insight.""",
        expected_output='A JSON array like: ["Insight 1", "Insight 2"]',
        agent=insight_generator,
        context=[summarize_task, analysis_task],
    )

    crew = Crew(
        agents=[summarizer, analyst, insight_generator],
        tasks=[summarize_task, analysis_task, insights_task],
        process=Process.sequential,
        verbose=True,
    )

    crew.kickoff()

    def parse_json(text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    question_summaries = parse_json(summarize_task.output.raw)
    analysis = parse_json(analysis_task.output.raw)
    insights = parse_json(insights_task.output.raw)

    return {
        "total_responses": total,
        "question_summaries": question_summaries,
        "themes": analysis.get("themes", []),
        "sentiment": analysis.get("sentiment", "neutral"),
        "insights": insights,
    }

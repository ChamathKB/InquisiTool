from crewai import LLM, Agent, Crew, Process, Task

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL
from inquisitool.tools.vector_search import QdrantSearchTool

qdrant_tool = QdrantSearchTool()

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.7,
    api_key=GEMINI_API_KEY,
)

router_llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.2,
    api_key=GEMINI_API_KEY,
)

question_generator = Agent(
    role="Campaign Question Generator",
    goal="Generate targeted survey questions for campaigns",
    backstory="""You are an expert survey designer who creates effective
        questions based on campaign objectives, target audience, and adapts
        follow-up questions based on previous user responses.""",
    tools=[qdrant_tool],
    llm=llm,
    verbose=True,
)

response_router = Agent(
    role="Response Router",
    goal="Decide the best direction for the next survey question based on the user's last answer",
    backstory="""You are an expert conversation analyst. You read survey responses and decide
        whether to probe deeper, ask for clarification, move to a new topic, redirect an
        off-topic answer, or close the survey early if enough has been covered.""",
    llm=router_llm,
    verbose=True,
)


def route_response(
    campaign: dict,
    questions: list,
    answers: list,
    questions_remaining: int,
    branch_delta: int,
) -> str:
    """
    Returns one of:
      CLOSE                     — end survey early (only when questions_remaining <= branch_delta)
      PROBE: <instruction>      — dig deeper into the last topic
      CLARIFY: <instruction>    — follow up on a vague/short answer
      CONTINUE: <instruction>   — move to a new topic
      REDIRECT: <instruction>   — bring user back to campaign scope
    """
    name = campaign.get("campaign_name", "")
    description = campaign.get("campaign_description", "")
    target_audience = campaign.get("target_audience", "")

    qa_pairs = "\n".join(
        f"Q{i+1}: {q}\nA{i+1}: {a or '(no answer)'}" for i, (q, a) in enumerate(zip(questions, answers))
    )
    last_answer = answers[-1] if answers else ""
    can_close = questions_remaining <= branch_delta

    close_instruction = (
        "You MAY output CLOSE if the conversation has covered the campaign objectives well "
        "and the last answer signals the user has nothing more to add. "
        "Only use CLOSE when truly warranted — do not close prematurely."
        if can_close
        else f"Do NOT output CLOSE — there are {questions_remaining} questions remaining and the "
        f"early-close window (delta={branch_delta}) has not been reached yet."
    )

    task = Task(
        description=f"""You are routing a survey conversation for campaign "{name}".
        Campaign description: {description}. Target audience: {target_audience}.

        Full conversation so far:
        {qa_pairs}

        Last answer: "{last_answer}"
        Questions remaining (including this turn): {questions_remaining}
        Branch delta: {branch_delta}

        {close_instruction}

        Decide the best direction and respond with EXACTLY one of these formats
        (no extra text, no markdown):
          CLOSE
          PROBE: <one sentence instruction for the question generator>
          CLARIFY: <one sentence instruction for the question generator>
          CONTINUE: <one sentence instruction for the question generator>
          REDIRECT: <one sentence instruction for the question generator>
        """,
        expected_output="A single routing directive in the exact format described.",
        agent=response_router,
    )

    crew = Crew(agents=[response_router], tasks=[task], process=Process.sequential, verbose=True)
    return crew.kickoff().raw.strip()


def generate_question(
    campaign: dict,
    question_turn: int,
    responses: list = [],
    branch_hint: str = "",
) -> str:
    name = campaign.get("campaign_name", "")
    description = campaign.get("campaign_description", "")
    target_audience = campaign.get("target_audience", "")
    collection_id = campaign.get("collection_id", "")

    hint_instruction = f"Branching instruction from the conversation router: {branch_hint}\n" if branch_hint else ""

    task = Task(
        description=f"""Generate survey question #{question_turn} for the campaign below.
        Campaign: {name}. Description: {description}. Target audience: {target_audience}.
        Use collection_name={collection_id} when searching the knowledge base.
        Previous responses: {responses or []}.
        {hint_instruction}Do not repeat topics already covered. Ask one focused question.""",
        expected_output="A single survey question.",
        agent=question_generator,
    )

    crew = Crew(agents=[question_generator], tasks=[task], process=Process.sequential, verbose=True)
    return crew.kickoff().raw


def generate_closing_message(campaign: dict) -> str:
    name = campaign.get("campaign_name", "this survey")
    description = campaign.get("campaign_description", "")
    target_audience = campaign.get("target_audience", "")

    task = Task(
        description=f"""Write a warm, concise thank-you message (2-3 sentences) to a survey participant.
        Campaign: {name}. Description: {description}. Audience: {target_audience}.
        Acknowledge their time, mention the campaign purpose, and express how their input helps.""",
        expected_output="A short, friendly closing message for the survey participant.",
        agent=question_generator,
    )

    crew = Crew(agents=[question_generator], tasks=[task], process=Process.sequential)
    return crew.kickoff().raw

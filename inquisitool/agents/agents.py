from crewai import LLM, Agent, Crew, Process, Task

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL
from inquisitool.tools.vector_search import QdrantSearchTool

qdrant_tool = QdrantSearchTool()

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.7,
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


def generate_question(campaign: dict, question_turn: int, responses: list = []) -> str:
    name = campaign.get("campaign_name", "")
    description = campaign.get("campaign_description", "")
    target_audience = campaign.get("target_audience", "")
    collection_id = campaign.get("collection_id", "")

    task = Task(
        description=f"""Generate survey question #{question_turn} for the campaign below.
        Campaign: {name}. Description: {description}. Target audience: {target_audience}.
        Use collection_name={collection_id} when searching the knowledge base.
        Previous responses: {responses or []}.
        Do not repeat topics already covered. Ask one focused question.""",
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

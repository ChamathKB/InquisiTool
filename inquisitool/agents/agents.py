from crewai import LLM, Agent, Crew, Process, Task
from pydantic import BaseModel

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL
from inquisitool.db.mongodb import get_campaign
from inquisitool.tools.campaign_tools import (
    CampaignDescriptionTool,
    QuestionCounterTool,
    TargetAudienceTool,
)
from inquisitool.tools.vector_search import QdrantSearchTool

question_counter_tool = QuestionCounterTool()
campaign_description_tool = CampaignDescriptionTool()
target_audience_tool = TargetAudienceTool()
qdrant_tool = QdrantSearchTool()

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.7,
    api_key=GEMINI_API_KEY,
)


class SurveyQuestion(BaseModel):
    question: str


campaign_manager = Agent(
    role="Survey Campaign Manager",
    goal="Manage and execute survey campaigns",
    backstory="""You are an expert campaign manager who can analyze campaign
    requirements and coordinate survey execution.""",
    tools=[question_counter_tool, campaign_description_tool, target_audience_tool],
    llm=llm,
    verbose=True,
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


campaign_management_task = Task(
    description="""Analyze and execute survey campaign {campaign_id}: validate campaign
    configuration including question count (use session_id {session_id}) and target audience,
    then return a single survey question based on the generated questions.""",
    expected_output="Confirmation of campaign readiness and any recommendations for optimization.",
    output_pydantic=SurveyQuestion,
    agent=campaign_manager,
)


question_generation_task = Task(
    description="""Generate survey question for campaign {campaign_id} based on
        campaign objectives, target audience, research context, and previous responses: {responses}.""",
    expected_output="A single survey question as a JSON object with a 'question' field.",
    agent=question_generator,
)


async def generate_question(campaign_id: str, session_id: str, responses: list = []) -> str:
    campaign = await get_campaign(campaign_id)
    collection_id = campaign.get("collection_id")

    question_crew = Crew(
        agents=[campaign_manager, question_generator],
        tasks=[campaign_management_task, question_generation_task],
        process=Process.sequential,
        verbose=True,
    )

    crew_output = question_crew.kickoff(
        inputs={
            "campaign_id": campaign_id,
            "session_id": session_id,
            "collection_id": collection_id,
            "responses": responses or [],
        }
    )

    if crew_output.pydantic:
        return crew_output.pydantic.question
    if crew_output.json_dict and "question" in crew_output.json_dict:
        return crew_output.json_dict["question"]
    return crew_output.raw

from crewai import LLM, Agent, Crew, Process, Task
from pydantic import BaseModel

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL
from inquisitool.db.mongodb import get_campaign
from inquisitool.tools.campaing_tools import (
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


campaign_manager = Agent(
    role="Survey Campaign Manager",
    goal="Manage and execute survey campaigns",
    backstory="""You are an expert campaign manager who can analyze campaign
    requirements and coordinate survey execution.""",
    tools=[question_counter_tool, campaign_description_tool, target_audience_tool],
    llm=llm,
    verbose=True,
)


survey_executor = Agent(
    role="Survey Execution Specialist",
    goal="Execute survey campaigns and collect responses",
    backstory="""You are a survey execution specialist who can run campaigns
    and manage the survey process efficiently.""",
    tools=[question_counter_tool, campaign_description_tool, target_audience_tool],
    llm=llm,
    verbose=True,
)


question_generation_task = Task(
    description="""Generate survey questions for campaign {campaign_id} based on
        campaign objectives, target audience, research context, and previous responses: {responses}.""",
    expected_output="A list of survey questions tailored to the campaign and previous responses.",
    agent=question_generator,
)


campaign_analysis_task = Task(
    description="""Analyze campaign {campaign_id} requirements and validate
    campaign configuration including question count and target audience.""",
    expected_output="Confirmation of campaign readiness and any recommendations for optimization.",
    agent=campaign_manager,
)


survey_execution_task = Task(
    description="""Execute survey campaign {campaign_id} by coordinating
    question delivery and response collection. Return a single survey question.""",
    expected_output="A single survey question as a JSON object with a 'question' field.",
    output_pydantic=SurveyQuestion,
    agent=survey_executor,
)


async def generate_question(campaign_id: str, responses: list = []) -> str:
    campaign = await get_campaign(campaign_id)
    collection_id = campaign.get("collection_id")

    question_crew = Crew(
        agents=[campaign_manager, question_generator, survey_executor],
        tasks=[campaign_analysis_task, question_generation_task, survey_execution_task],
        process=Process.sequential,
        verbose=True,
    )

    crew_output = question_crew.kickoff(
        inputs={"campaign_id": campaign_id, "collection_id": collection_id, "responses": responses or []}
    )

    if crew_output.pydantic:
        return crew_output.pydantic.question
    if crew_output.json_dict and "question" in crew_output.json_dict:
        return crew_output.json_dict["question"]
    return crew_output.raw

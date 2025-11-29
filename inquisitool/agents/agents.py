from crewai import LLM, Agent, Crew, Process, Task
from qdrant_client import QdrantClient

from inquisitool.constants import LLM_MODEL
from inquisitool.tools.campaing_tools import QuestionCounterTool
from inquisitool.tools.vector_search import qdrant_tool

qdrant_tool = qdrant_tool(pdf_path="inquisitool.pdf", qdrant=QdrantClient, collection_name="inquisitool")
question_counter_tool = QuestionCounterTool()

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.7,
)

search_agent = Agent(
    role="Senior Semantic Search Agent",
    goal="Find and analyze documents based on semantic search",
    backstory="""You are an expert research assistant who can find relevant
    information using semantic search in a Qdrant database.""",
    tools=[qdrant_tool],
    llm=llm,
    verbose=True,
)

answer_agent = Agent(
    role="Senior Answer Assistant",
    goal="Generate answers to questions based on the context provided",
    backstory="""You are an expert answer assistant who can generate
    answers to questions based on the context provided.""",
    tools=[qdrant_tool],
    llm=llm,
    verbose=True,
)

campaign_manager = Agent(
    role="Survey Campaign Manager",
    goal="Manage and execute survey campaigns",
    backstory="""You are an expert campaign manager who can analyze campaign
    requirements and coordinate survey execution.""",
    tools=[question_counter_tool],
    llm=llm,
    verbose=True,
)

survey_executor = Agent(
    role="Survey Execution Specialist",
    goal="Execute survey campaigns and collect responses",
    backstory="""You are a survey execution specialist who can run campaigns
    and manage the survey process efficiently.""",
    tools=[question_counter_tool],
    llm=llm,
    verbose=True,
)

search_task = Task(
    description="""Search for relevant documents about the {query}.
    Your final answer should include:
    - The relevant information found
    - The similarity scores of the results
    - The metadata of the relevant documents""",
    agent=search_agent,
)

answer_task = Task(
    description="""Given the context and metadata of relevant documents,
    generate a final answer based on the context.""",
    agent=answer_agent,
)

campaign_analysis_task = Task(
    description="""Analyze campaign {campaign_id} requirements and validate
    campaign configuration including question count and target audience.""",
    agent=campaign_manager,
)

survey_execution_task = Task(
    description="""Execute survey campaign {campaign_id} by coordinating
    question delivery and response collection.""",
    agent=survey_executor,
)

crew = Crew(
    agents=[search_agent, answer_agent],
    tasks=[search_task, answer_task],
    process=Process.sequential,
    verbose=True,
)

campaign_crew = Crew(
    agents=[campaign_manager, survey_executor],
    tasks=[campaign_analysis_task, survey_execution_task],
    process=Process.sequential,
    verbose=True,
)


def ask(query: str) -> str:
    return crew.kickoff(inputs={"query": query})


def run_campaign(campaign_id: str) -> str:
    return campaign_crew.kickoff(inputs={"campaign_id": campaign_id})

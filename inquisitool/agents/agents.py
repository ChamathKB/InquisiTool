from crewai import Agent, Task, Crew, Process, LLM
from inquisitool.tools.vector_search import qdrant_tool
from inquisitool.constants import LLM_MODEL

qdrant_tool = qdrant_tool("inquisitool.pdf", "inquisitool")

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
    verbose=True
)

answer_agent = Agent(
    role="Senior Answer Assistant",
    goal="Generate answers to questions based on the context provided",
    backstory="""You are an expert answer assistant who can generate 
    answers to questions based on the context provided.""",
    tools=[qdrant_tool],
    llm=llm,
    verbose=True
)

search_task = Task(
    description="""Search for relevant documents about the {query}.
    Your final answer should include:
    - The relevant information found
    - The similarity scores of the results
    - The metadata of the relevant documents""",
    agent=search_agent
)

answer_task = Task(
    description="""Given the context and metadata of relevant documents,
    generate a final answer based on the context.""",
    agent=answer_agent
)

crew = Crew(
    agents=[search_agent, answer_agent],
    tasks=[search_task, answer_task],
    process=Process.sequential,
    verbose=True,
)

def ask(query: str) -> str:
    return crew.kickoff(inputs={"query": query})

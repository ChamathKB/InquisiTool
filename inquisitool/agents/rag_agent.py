from crewai import LLM, Agent, Crew, Process, Task

from inquisitool.constants import GEMINI_API_KEY, LLM_MODEL, QDRANT_URL
from inquisitool.tools.vector_search import QdrantSearchTool, get_embeddings

llm = LLM(
    model=f"gemini/{LLM_MODEL}",
    temperature=0.2,
    api_key=GEMINI_API_KEY,
)

qdrant_tool = QdrantSearchTool()

rag_agent = Agent(
    role="Knowledge Base Assistant",
    goal="Answer questions accurately using only information retrieved from the knowledge base",
    backstory="""You are a precise research assistant. You search the knowledge base for relevant
        information and provide grounded, accurate answers. If the knowledge base does not contain
        enough information to answer, you say so clearly rather than guessing.""",
    tools=[qdrant_tool],
    llm=llm,
    verbose=True,
)


def _format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    return "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in history)


def answer_question(collection_id: str, question: str, history: list = []) -> tuple[str, list]:
    """
    Returns (answer, sources) where sources is a list of {"text": str, "score": float}.
    Sources are retrieved directly from Qdrant so we can return them alongside the answer.
    """
    from qdrant_client import QdrantClient

    qdrant = QdrantClient(url=QDRANT_URL)
    query_vector = get_embeddings(question)
    results = qdrant.query_points(
        collection_name=collection_id,
        query=query_vector,
        limit=4,
        score_threshold=0.35,
    ).points

    sources = [{"text": r.payload.get("text", ""), "score": round(r.score, 3)} for r in results]

    context = (
        "\n\n".join(f"[Source {i+1} | score={s['score']}]\n{s['text']}" for i, s in enumerate(sources))
        or "No relevant documents found in the knowledge base."
    )

    history_text = _format_history(history)

    task = Task(
        description=f"""Answer the user's question using ONLY the context below.
        If the context does not contain enough information, say so clearly.
        Do not fabricate information.

        Conversation history:
        {history_text}

        Retrieved context:
        {context}

        User question: {question}

        Provide a clear, concise answer. Reference source numbers (e.g. [Source 1]) where relevant.""",
        expected_output="A grounded answer to the user's question based on the retrieved context.",
        agent=rag_agent,
    )

    crew = Crew(agents=[rag_agent], tasks=[task], process=Process.sequential, verbose=True)
    answer = crew.kickoff().raw

    return answer, sources

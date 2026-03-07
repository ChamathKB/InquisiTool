import uuid

import pdfplumber
from crewai_tools import QdrantVectorSearchTool
from crewai_tools.tools.qdrant_vector_search_tool.qdrant_search_tool import QdrantConfig
from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from inquisitool.constants import EMBEDDING_MODEL, GEMINI_API_KEY, QDRANT_URL

embeddings = genai.Client(api_key=GEMINI_API_KEY)


def get_embeddings(text: str) -> list[float]:
    """
    Get embeddings for a given text using Gemini embedding model
    Args:
        text (str): Text to get embeddings for
    Returns:
        list[float]: Embeddings for the given text
    """
    result = embeddings.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=1536,
        ),
    )
    return result.embeddings[0].values


def extract_text_from_pdf(pdf_path: str) -> list[str]:
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text.strip())
    return text


def create_collection(qdrant: QdrantClient, collection_name: str) -> dict:
    try:
        if not qdrant.collection_exists(collection_name):
            qdrant.create_collection(
                collection_name=collection_name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        return {"message": "Collection created successfully!"}
    except Exception as e:
        return {"error": str(e)}


def delete_collection(qdrant: QdrantClient, collection_id: str) -> dict:
    try:
        if qdrant.collection_exists(collection_id):
            qdrant.delete_collection(collection_id)
        return {"message": "Collection deleted successfully!"}
    except Exception as e:
        return {"error": str(e)}


def load_pdf_to_qdrant(pdf_path: str, qdrant: QdrantClient, collection_name: str) -> None:

    text_chunks = extract_text_from_pdf(pdf_path)

    if qdrant.collection_exists(collection_name):
        points = []
        for chunk in text_chunks:
            embedding = get_embeddings(chunk)
            points.append(PointStruct(id=str(uuid.uuid4()), vector=embedding, payload={"text": chunk}))
        qdrant.upsert(collection_name=collection_name, points=points)


def qdrant_tool(collection_name: str) -> QdrantVectorSearchTool:

    qdrant_tool = QdrantVectorSearchTool(
        qdrant_config=QdrantConfig(
            qdrant_url=QDRANT_URL,
            # qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=collection_name,
            limit=3,
            score_threshold=0.35,
        )
    )
    return qdrant_tool

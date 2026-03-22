import uuid
from typing import Type

import pdfplumber
from crewai.tools import BaseTool
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
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


class QdrantSearchInput(BaseModel):
    """Input schema for QdrantSearchTool."""

    query: str = Field(..., description="The search query to find relevant documents")
    collection_name: str = Field(..., description="The name of the Qdrant collection to search in")


class QdrantSearchTool(BaseTool):
    name: str = "qdrant_search"
    description: str = "Search for relevant documents in the knowledge base using semantic search"
    args_schema: Type[BaseModel] = QdrantSearchInput
    # collection_name: str

    def _run(self, query: str, collection_name: str) -> str:
        """Search Qdrant collection for relevant documents"""
        try:
            qdrant = QdrantClient(url=QDRANT_URL)
            query_vector = get_embeddings(query)
            results = qdrant.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=3,
                score_threshold=0.35,
            )
            if not results:
                return "No relevant documents found."

            output = []
            for result in results:
                output.append(f"Score: {result.score}\nContent: {result.payload.get('text', '')}")
            return "\n\n".join(output)
        except Exception as e:
            return f"Search error: {str(e)}"


def qdrant_tool(collection_name: str) -> QdrantSearchTool:
    return QdrantSearchTool(collection_name=collection_name)

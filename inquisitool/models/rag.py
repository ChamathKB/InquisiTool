from typing import List

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class RAGRequest(BaseModel):
    collection_id: str
    question: str
    history: List[ChatMessage] = []


class RAGSource(BaseModel):
    text: str
    score: float


class RAGResponse(BaseModel):
    answer: str
    sources: List[RAGSource]

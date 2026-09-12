from datetime import datetime
from typing import List

from pydantic import BaseModel


class QuestionSummary(BaseModel):
    question: str
    summary: str


class AnalysisReport(BaseModel):
    campaign_id: str
    total_responses: int
    question_summaries: List[QuestionSummary]
    themes: List[str]
    sentiment: str
    insights: List[str]
    generated_at: datetime

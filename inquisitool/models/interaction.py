from typing import Optional

from pydantic import BaseModel


class SurveyRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    campaign_id: str
    answer: Optional[str] = None


class SurveyResponse(BaseModel):
    session_id: str
    session_number: int
    question: str
    question_count: int
    survey_ended: bool

from typing import List, Optional

from pydantic import BaseModel


class DesignerMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class DesignerConfig(BaseModel):
    campaign_name: str
    campaign_description: str
    target_audience: str
    number_of_questions: int
    branch_delta: int
    status: str
    start_date: str  # ISO datetime string
    end_date: str  # ISO datetime string


class DesignerRequest(BaseModel):
    message: str
    history: List[DesignerMessage] = []


class DesignerResponse(BaseModel):
    message: str
    is_complete: bool
    config: Optional[DesignerConfig] = None

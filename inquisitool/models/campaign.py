from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    campaign_name: str
    campaign_description: str
    start_date: datetime
    end_date: datetime
    status: str
    target_audience: str
    number_of_questions: int
    branch_delta: int = 2
    collection_id: str
    allowed_origins: List[str] = []


class CampaignUpdate(BaseModel):
    campaign_name: str | None = None
    campaign_description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: str | None = None
    target_audience: str | None = None
    number_of_questions: int | None = None
    branch_delta: int | None = None
    collection_id: str | None = None
    allowed_origins: List[str] | None = None


class CampaignResponse(BaseModel):
    campaign_id: UUID
    campaign_name: str
    campaign_description: str
    start_date: datetime
    end_date: datetime
    status: str
    target_audience: str
    number_of_questions: int
    branch_delta: int = 2
    collection_id: str
    created_at: datetime
    updated_at: datetime
    api_key: str | None = None
    allowed_origins: List[str] = []

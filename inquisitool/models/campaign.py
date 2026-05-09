from datetime import datetime
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
    collection_id: str


class CampaignResponse(BaseModel):
    campaign_id: UUID
    campaign_name: str
    campaign_description: str
    start_date: datetime
    end_date: datetime
    status: str
    target_audience: str
    number_of_questions: int
    collection_id: str
    created_at: datetime
    updated_at: datetime

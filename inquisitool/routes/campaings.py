from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from inquisitool.db.mongodb import (
    create_campaign,
    delete_campaign,
    get_campaign,
    list_campaigns,
    update_campaign,
)

router = APIRouter()


# Pydantic model for Campaign
class Campaign(BaseModel):
    campaign_name: str
    campaign_description: str
    start_date: datetime
    end_date: datetime
    status: str
    target_audience: str
    number_of_questions: int
    collection_id: str  # Assigned knowledge base collection


# Pydantic model for Campaign Response
class CampaignResponse(BaseModel):
    campaign_id: UUID
    campaign_name: str
    campaign_description: str
    start_date: datetime
    end_date: datetime
    status: str
    target_audience: str
    number_of_questions: int
    collection_id: str  # Assigned knowledge base collection
    created_at: datetime
    updated_at: datetime


# Create campaign
@router.post("/campaigns/", response_model=CampaignResponse)
async def create_campaign_endpoint(campaign: Campaign):
    result = await create_campaign(campaign.model_dump())
    return await get_campaign(result["campaign_id"])


# Get all campaigns
@router.get("/campaigns/", response_model=List[CampaignResponse])
async def get_campaigns():
    try:
        result = await list_campaigns()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign listing failed: {e}")


# Get campaign by ID
@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign_endpoint(campaign_id: str):
    try:
        return await get_campaign(campaign_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Campaign not found: {e}")


# Update campaign
@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign_endpoint(campaign_id: str, updated_campaign: Campaign):
    try:
        await update_campaign(campaign_id, updated_campaign.model_dump())
        return await get_campaign(campaign_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Campaign not found: {e}")


# Delete campaign
@router.delete("/campaigns/{campaign_id}")
async def delete_campaign_endpoint(campaign_id: str):
    result = await delete_campaign(campaign_id)
    if result:
        return {"message": "Campaign deleted successfully"}
    raise HTTPException(status_code=404, detail="Campaign not found")

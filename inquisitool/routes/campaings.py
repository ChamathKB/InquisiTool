from datetime import datetime
from typing import List
from uuid import UUID

from db.mongodb import (
    create_campaign,
    delete_campaign,
    list_campaigns,
    update_campaign,
)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


# Pydantic model for Campaign
class Campaign(BaseModel):
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
@app.post("/campaigns/", response_model=Campaign)
async def create_campaign_endpoint(campaign: Campaign):
    result = await create_campaign(campaign)
    return result


# Get all campaigns
@app.get("/campaigns/", response_model=List[Campaign])
async def get_campaigns():
    return await list_campaigns()


# Get campaign by ID
@app.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: UUID):
    campaigns = await list_campaigns()
    for campaign in campaigns:
        if campaign.campaign_id == campaign_id:
            return campaign
    raise HTTPException(status_code=404, detail="Campaign not found")


# Update campaign
@app.put("/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign_endpoint(campaign_id: UUID, updated_campaign: Campaign):
    result = await update_campaign(campaign_id, updated_campaign)
    if result:
        return updated_campaign
    raise HTTPException(status_code=404, detail="Campaign not found")


# Delete campaign
@app.delete("/campaigns/{campaign_id}")
async def delete_campaign_endpoint(campaign_id: UUID):
    result = await delete_campaign(campaign_id)
    if result:
        return {"message": "Campaign deleted successfully"}
    raise HTTPException(status_code=404, detail="Campaign not found")

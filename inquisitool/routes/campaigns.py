import logging
from typing import List

from fastapi import APIRouter, HTTPException

from inquisitool.db.mongodb import (
    create_campaign,
    delete_campaign,
    get_campaign,
    list_campaigns,
    update_campaign,
)
from inquisitool.models.campaign import CampaignCreate, CampaignResponse, CampaignUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=CampaignResponse)
async def create_campaign_endpoint(campaign: CampaignCreate):
    result = await create_campaign(campaign.model_dump())
    logger.info("Campaign created: %s", result["campaign_id"])
    return await get_campaign(result["campaign_id"])


@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns():
    try:
        return await list_campaigns()
    except Exception as e:
        logger.error("Failed to list campaigns: %s", e)
        raise HTTPException(status_code=500, detail=f"Campaign listing failed: {e}")


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign_endpoint(campaign_id: str):
    try:
        return await get_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign_endpoint(campaign_id: str, updated_campaign: CampaignUpdate):
    try:
        await update_campaign(campaign_id, updated_campaign.model_dump(exclude_none=True))
        logger.info("Campaign updated: %s", campaign_id)
        return await get_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to update campaign %s: %s", campaign_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
async def delete_campaign_endpoint(campaign_id: str):
    try:
        await delete_campaign(campaign_id)
        return {"message": "Campaign deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete campaign %s: %s", campaign_id, e)
        raise HTTPException(status_code=500, detail=str(e))

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


@router.post(
    "/create_campaign",
    response_model=CampaignResponse,
    summary="Create a campaign",
    description="Creates a new survey campaign with the provided configuration.",
    responses={500: {"description": "Internal server error"}},
)
async def create_campaign_endpoint(campaign: CampaignCreate):
    result = await create_campaign(campaign.model_dump())
    logger.info("Campaign created: %s", result["campaign_id"])
    return await get_campaign(result["campaign_id"])


@router.get(
    "/list_campaigns",
    response_model=List[CampaignResponse],
    summary="List all campaigns",
    description="Returns a list of all campaigns.",
    responses={500: {"description": "Internal server error"}},
)
async def get_campaigns():
    try:
        return await list_campaigns()
    except Exception as e:
        logger.error("Failed to list campaigns: %s", e)
        raise HTTPException(status_code=500, detail=f"Campaign listing failed: {e}")


@router.get(
    "/get_campaign/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get a campaign",
    description="Retrieves a single campaign by its ID.",
    responses={404: {"description": "Campaign not found"}, 500: {"description": "Internal server error"}},
)
async def get_campaign_endpoint(campaign_id: str):
    try:
        return await get_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/update_campaign/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update a campaign",
    description="Partially updates a campaign. Only the fields provided in the request body will be updated.",
    responses={404: {"description": "Campaign not found"}, 500: {"description": "Internal server error"}},
)
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


@router.delete(
    "/delete_campaign/{campaign_id}",
    summary="Delete a campaign",
    description="Permanently deletes a campaign by its ID.",
    responses={404: {"description": "Campaign not found"}, 500: {"description": "Internal server error"}},
)
async def delete_campaign_endpoint(campaign_id: str):
    try:
        await delete_campaign(campaign_id)
        return {"message": "Campaign deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete campaign %s: %s", campaign_id, e)
        raise HTTPException(status_code=500, detail=str(e))

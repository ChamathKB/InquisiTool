import logging
import secrets
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from inquisitool.agents.analysis_crew import analyze_campaign
from inquisitool.db.mongodb import (
    create_campaign,
    delete_campaign,
    get_analysis,
    get_campaign,
    list_campaigns,
    list_completed_interactions,
    save_analysis,
    update_campaign,
)
from inquisitool.models.analysis import AnalysisReport
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


@router.post(
    "/{campaign_id}/generate_key",
    response_model=CampaignResponse,
    summary="Generate a widget API key",
    description="Generates (or regenerates) a shareable API key for the campaign widget.",
    responses={404: {"description": "Campaign not found"}, 500: {"description": "Internal server error"}},
)
async def generate_api_key(campaign_id: str):
    try:
        api_key = secrets.token_urlsafe(32)
        await update_campaign(campaign_id, {"api_key": api_key})
        logger.info("API key generated for campaign: %s", campaign_id)
        return await get_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to generate API key for campaign %s: %s", campaign_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{campaign_id}/analyze",
    response_model=AnalysisReport,
    summary="Analyze campaign responses",
    description="Runs a CrewAI analysis over all completed survey sessions for the campaign and saves the report.",
    responses={
        404: {"description": "Campaign not found"},
        422: {"description": "Not enough completed responses to analyze"},
        500: {"description": "Internal server error"},
    },
)
async def analyze_campaign_endpoint(campaign_id: str):
    try:
        campaign = await get_campaign(campaign_id)
        interactions = await list_completed_interactions(campaign_id)
        if not interactions:
            raise HTTPException(status_code=422, detail="No completed survey responses found for this campaign.")
        result = analyze_campaign(campaign, interactions)
        report = {
            "campaign_id": campaign_id,
            "generated_at": datetime.now(timezone.utc),
            **result,
        }
        await save_analysis(campaign_id, report)
        logger.info("Analysis saved for campaign: %s", campaign_id)
        return AnalysisReport(**report)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Analysis failed for campaign %s: %s", campaign_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{campaign_id}/analysis",
    response_model=AnalysisReport,
    summary="Get campaign analysis report",
    description="Returns the most recent analysis report for the campaign.",
    responses={
        404: {"description": "Campaign or analysis not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_analysis_endpoint(campaign_id: str):
    try:
        report = await get_analysis(campaign_id)
        if report is None:
            raise HTTPException(status_code=404, detail="No analysis found. Run POST /{campaign_id}/analyze first.")
        return AnalysisReport(**report)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get analysis for campaign %s: %s", campaign_id, e)
        raise HTTPException(status_code=500, detail=str(e))

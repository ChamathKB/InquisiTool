from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pymongo import MongoClient

from inquisitool.constants import MONGO_DB_NAME, MONGO_URL


class CampaignDescriptionInput(BaseModel):
    """Input schema for CampaignDescriptionTool."""

    campaign_id: str = Field(..., description="The campaign ID to get description for")


class CampaignDescriptionTool(BaseTool):
    name: str = "campaign_description"
    description: str = "Get the description of a specific campaign"
    args_schema: Type[BaseModel] = CampaignDescriptionInput

    def _run(self, campaign_id: str) -> dict:
        """Get description for a specific campaign"""
        try:
            with MongoClient(MONGO_URL) as client:
                campaign = client[MONGO_DB_NAME]["campaigns"].find_one({"campaign_id": campaign_id})
            if campaign is None:
                return {"error": "Campaign not found", "campaign_id": campaign_id, "campaign_description": None}
            return {"campaign_id": campaign_id, "description": campaign.get("campaign_description", "")}
        except Exception as e:
            return {"error": f"Database error: {e}", "campaign_id": campaign_id, "campaign_description": None}


class TargetAudienceInput(BaseModel):
    """Input schema for TargetAudienceTool."""

    campaign_id: str = Field(..., description="The campaign ID to get target audience for")


class TargetAudienceTool(BaseTool):
    name: str = "target_audience"
    description: str = "Get the target audience of a specific campaign"
    args_schema: Type[BaseModel] = TargetAudienceInput

    def _run(self, campaign_id: str) -> dict:
        """Get target audience for a specific campaign"""
        try:
            with MongoClient(MONGO_URL) as client:
                campaign = client[MONGO_DB_NAME]["campaigns"].find_one({"campaign_id": campaign_id})
            if campaign is None:
                return {"error": "Campaign not found", "campaign_id": campaign_id, "target_audience": None}
            return {"campaign_id": campaign_id, "target_audience": campaign.get("target_audience", "")}
        except Exception as e:
            return {"error": f"Database error: {e}", "campaign_id": campaign_id, "target_audience": None}


class QuestionCounterInput(BaseModel):
    """Input schema for QuestionCounterTool."""

    campaign_id: str = Field(..., description="The campaign ID to count questions for")
    session_id: str = Field(..., description="The session ID to get current question count for")


class QuestionCounterTool(BaseTool):
    name: str = "question_counter"
    description: str = "Get the configured question limit for a campaign and the current question count for a session"
    args_schema: Type[BaseModel] = QuestionCounterInput

    def _run(self, campaign_id: str, session_id: str) -> dict:
        """Get question limit and current count for a campaign session"""
        try:
            with MongoClient(MONGO_URL) as client:
                db = client[MONGO_DB_NAME]
                campaign = db["campaigns"].find_one({"campaign_id": campaign_id})
                if campaign is None:
                    return {"error": "Campaign not found", "campaign_id": campaign_id}
                interaction = db["campaign_interactions"].find_one({"session_id": session_id})
                current_count = interaction.get("question_count", 0) if interaction else 0
            return {
                "campaign_id": campaign_id,
                "session_id": session_id,
                "question_limit": campaign.get("number_of_questions", 0),
                "current_question_count": current_count,
            }
        except Exception as e:
            return {"error": f"Database error: {e}", "campaign_id": campaign_id}

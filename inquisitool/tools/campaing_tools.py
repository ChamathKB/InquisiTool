from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pymongo import MongoClient

from inquisitool.constants import MONGO_DB_NAME, MONGO_URL


class QuestionCounterInput(BaseModel):
    """Input schema for QuestionCounterTool."""

    campaign_id: str = Field(..., description="The campaign ID to count questions for")


class QuestionCounterTool(BaseTool):
    name: str = "question_counter"
    description: str = "Count the number of questions for a specific campaign"
    args_schema: Type[BaseModel] = QuestionCounterInput

    def _run(self, campaign_id: str) -> dict:
        """Count number of questions for a specific campaign"""
        try:
            with MongoClient(MONGO_URL) as client:
                campaign = client[MONGO_DB_NAME]["campaigns"].find_one({"campaign_id": campaign_id})
            if campaign is None:
                return {"error": "Campaign not found", "campaign_id": campaign_id, "total_questions": 0}
            return {"campaign_id": campaign_id, "total_questions": campaign.get("number_of_questions", 0)}
        except Exception as e:
            return {"error": f"Database error: {e}", "campaign_id": campaign_id, "total_questions": 0}

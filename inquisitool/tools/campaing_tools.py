from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from inquisitool.db.mongodb import get_campaign


class QuestionCounterInput(BaseModel):
    """Input schema for QuestionCounterTool."""

    campaign_id: str = Field(..., description="The campaign ID to count questions for")


class QuestionCounterTool(BaseTool):
    name: str = "question_counter"
    description: str = "Count the number of questions for a specific campaign"
    args_schema: Type[BaseModel] = QuestionCounterInput

    async def _run(self, campaign_id: str) -> dict:
        """Count number of questions for a specific campaign"""
        try:
            campaign = await get_campaign(campaign_id)
            question_count = campaign.get("number_of_questions", 0)
            return {"campaign_id": campaign_id, "total_questions": question_count}
        except Exception as e:
            return {"error": f"Database error: {e}", "campaign_id": campaign_id, "total_questions": 0}

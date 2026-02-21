import logging

from inquisitool.db.mongodb import get_campaign, update_interaction


async def check_question_limit(campaign_id: str, question_count: int) -> bool:
    """
    Check if the question limit for the campaign has been reached
    """
    try:
        campaign = await get_campaign(campaign_id)
        return question_count >= campaign.get("number_of_questions", 0)
    except Exception as e:
        logging.error(f"Error checking question limit: {e}")
        return False


async def end_survey(session_id: str) -> None:
    """
    Mark survey as completed for the given session
    """
    await update_interaction(session_id, {"survey_ended": True})

from inquisitool.db.mongodb import update_interaction


async def end_survey(session_id: str) -> None:
    await update_interaction(session_id, {"survey_ended": True})

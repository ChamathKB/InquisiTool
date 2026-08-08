import logging
import uuid

from fastapi import APIRouter, Header, HTTPException, Request

from inquisitool.agents.agents import generate_closing_message, generate_question
from inquisitool.db.mongodb import (
    create_interaction,
    get_campaign_by_api_key,
    get_interaction,
    update_interaction,
)
from inquisitool.db.redis import cache_delete, cache_get, cache_set, interaction_key
from inquisitool.models.interaction import SurveyRequest, SurveyResponse
from inquisitool.utils import end_survey

router = APIRouter()
logger = logging.getLogger(__name__)

ANONYMOUS_USER_ID = str(uuid.UUID(int=0))


async def _resolve_campaign(api_key: str) -> dict:
    try:
        return await get_campaign_by_api_key(api_key)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post(
    "/survey",
    response_model=SurveyResponse,
    summary="Public survey interaction (widget)",
    description="Same as /query/survey but authenticated via X-API-Key campaign token. User is anonymous.",
)
async def public_survey(body: SurveyRequest, request: Request, x_api_key: str = Header(...)):
    campaign = await _resolve_campaign(x_api_key)

    # Override user_id — always anonymous
    body = body.model_copy(update={"user_id": ANONYMOUS_USER_ID})

    try:
        redis = request.app.state.redis_client
        is_new = body.session_id is None

        if is_new:
            result = await create_interaction(
                {
                    "campaign_id": body.campaign_id,
                    "user_id": body.user_id,
                    "campaign": campaign,
                    "answers": [],
                    "questions": [],
                    "question_count": 0,
                    "survey_ended": False,
                }
            )
            session_id = result["session_id"]
            session_number = result["session_number"]
            question = generate_question(campaign, question_turn=1)
            await update_interaction(session_id, {"questions": [question], "question_count": 1})
            return SurveyResponse(
                session_id=session_id,
                session_number=session_number,
                question=question,
                question_count=1,
                survey_ended=False,
            )

        interaction = await cache_get(redis, interaction_key(body.session_id))  # type: ignore
        if interaction is None:
            interaction = await get_interaction(body.session_id)  # type: ignore
            await cache_set(redis, interaction_key(body.session_id), interaction)  # type: ignore

        session_id = body.session_id
        session_number = interaction.get("session_number", 1)
        campaign = interaction.get("campaign")  # type: ignore
        answers = interaction.get("answers", [])
        answers.append(body.answer)
        questions = interaction.get("questions", [])
        question_count = len(questions)
        question_limit = campaign.get("number_of_questions", 0)

        if question_count >= question_limit:
            closing_message = generate_closing_message(campaign)
            await update_interaction(session_id, {"answers": answers, "survey_ended": True})
            await cache_delete(redis, interaction_key(session_id))
            await end_survey(session_id)
            return SurveyResponse(
                session_id=session_id,
                session_number=session_number,
                question=closing_message,
                question_count=question_count,
                survey_ended=True,
            )

        question_turn = question_count + 1
        question = generate_question(campaign, question_turn, answers)
        questions.append(question)
        updated = {"answers": answers, "questions": questions, "question_count": question_turn}
        await update_interaction(session_id, updated)
        await cache_set(redis, interaction_key(session_id), {**interaction, **updated})

        return SurveyResponse(
            session_id=session_id,
            session_number=session_number,
            question=question,
            question_count=question_turn,
            survey_ended=False,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Public survey error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

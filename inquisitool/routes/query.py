from fastapi import APIRouter, HTTPException, Request

from inquisitool.agents.agents import generate_closing_message, generate_question
from inquisitool.auth import limiter
from inquisitool.db.mongodb import (
    create_interaction,
    get_campaign,
    get_interaction,
    update_interaction,
)
from inquisitool.db.redis import (
    cache_delete,
    cache_get,
    cache_set,
    campaign_key,
    interaction_key,
)
from inquisitool.models.interaction import SurveyRequest, SurveyResponse
from inquisitool.utils import end_survey

router = APIRouter()


@router.post("/survey", response_model=SurveyResponse)
@limiter.limit("30/minute")
async def process_survey(request: SurveyRequest, req: Request):
    try:
        redis = req.app.state.redis_client
        is_new = request.session_id is None

        if is_new:
            campaign = await cache_get(redis, campaign_key(request.campaign_id))
            if campaign is None:
                campaign = await get_campaign(request.campaign_id)
                await cache_set(redis, campaign_key(request.campaign_id), campaign)
            result = await create_interaction(
                {
                    "campaign_id": request.campaign_id,
                    "user_id": request.user_id,
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

        interaction = await cache_get(redis, interaction_key(request.session_id))  # type: ignore
        if interaction is None:
            interaction = await get_interaction(request.session_id)  # type: ignore
            await cache_set(redis, interaction_key(request.session_id), interaction)  # type: ignore
        session_id = request.session_id
        session_number = interaction.get("session_number", 1)
        campaign = interaction.get("campaign")  # type: ignore
        answers = interaction.get("answers", [])
        answers.append(request.answer)
        questions = interaction.get("questions", [])
        question_count = len(questions)
        question_limit = campaign.get("number_of_questions", 0)  # type: ignore

        if question_count >= question_limit:
            closing_message = generate_closing_message(campaign)  # type: ignore
            await update_interaction(session_id, {"answers": answers, "survey_ended": True})
            await cache_delete(redis, interaction_key(session_id))  # type: ignore
            await end_survey(session_id)
            return SurveyResponse(
                session_id=session_id,
                session_number=session_number,
                question=closing_message,
                question_count=question_count,
                survey_ended=True,
            )

        question_turn = question_count + 1
        question = generate_question(campaign, question_turn, answers)  # type: ignore
        questions.append(question)
        updated = {"answers": answers, "questions": questions, "question_count": question_turn}
        await update_interaction(session_id, updated)
        await cache_set(redis, interaction_key(session_id), {**interaction, **updated})  # type: ignore

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
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException

from inquisitool.agents.agents import generate_closing_message, generate_question
from inquisitool.db.mongodb import (
    create_interaction,
    get_campaign,
    get_interaction,
    update_interaction,
)
from inquisitool.models.interaction import SurveyRequest, SurveyResponse
from inquisitool.utils import end_survey

router = APIRouter()


@router.post("/survey", response_model=SurveyResponse)
async def process_survey(request: SurveyRequest):
    try:
        is_new = request.session_id is None

        if is_new:
            campaign = await get_campaign(request.campaign_id)
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

        interaction = await get_interaction(request.session_id)  # type: ignore
        session_id = request.session_id
        session_number = interaction.get("session_number", 1)
        campaign = interaction.get("campaign")  # type: ignore
        answers = interaction.get("answers", [])
        answers.append(request.answer)
        questions = interaction.get("questions", [])
        question_count = len(questions)
        question_limit = campaign.get("number_of_questions", 0)

        if question_count >= question_limit:
            closing_message = generate_closing_message(campaign)
            await update_interaction(session_id, {"answers": answers, "survey_ended": True})
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
        await update_interaction(
            session_id, {"answers": answers, "questions": questions, "question_count": question_turn}
        )

        return SurveyResponse(
            session_id=session_id,
            session_number=session_number,
            question=question,
            question_count=question_turn,
            survey_ended=False,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

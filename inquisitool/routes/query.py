from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from inquisitool.agents.agents import generate_closing_message, generate_question
from inquisitool.db.mongodb import (
    create_interaction,
    get_interaction,
    update_interaction,
)
from inquisitool.utils import check_question_limit, end_survey

router = APIRouter()


class SurveyRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None  # None = new session, server generates it
    campaign_id: str
    answer: Optional[str] = None


class SurveyResponse(BaseModel):
    session_id: str
    session_number: int
    question: str
    question_count: int
    survey_ended: bool


@router.post("/survey", response_model=SurveyResponse)
async def process_survey(request: SurveyRequest):
    try:
        # Check if this is a new session (no session_id) or existing (has session_id + answer)
        is_new = request.session_id is None
        if not is_new:
            interaction = await get_interaction(request.session_id)  # type: ignore

        if is_new:
            # Create new interaction — server generates session_id
            interaction_data = {
                "campaign_id": request.campaign_id,
                "user_id": request.user_id,
                "answers": [],
                "questions": [],
                "question_count": 0,
                "survey_ended": False,
            }
            result = await create_interaction(interaction_data)
            session_id = result["session_id"]
            session_number = result["session_number"]
            question = await generate_question(
                campaign_id=request.campaign_id, session_id=session_id, responses=["/start"]
            )
            await update_interaction(session_id, {"questions": [question], "question_count": 1})
            return SurveyResponse(
                session_id=session_id,
                session_number=session_number,
                question=question,
                question_count=1,
                survey_ended=False,
            )

        # Handle answer
        answers = interaction.get("answers", [])
        answers.append(request.answer)
        questions = interaction.get("questions", [])
        question_count = len(questions)

        session_id = request.session_id
        session_number = interaction.get("session_number", 1)

        # Check if limit reached
        survey_ended = await check_question_limit(request.campaign_id, question_count)

        if survey_ended:
            closing_message = await generate_closing_message(request.campaign_id)
            await update_interaction(session_id, {"answers": answers, "survey_ended": True})
            await end_survey(session_id)
            return SurveyResponse(
                session_id=session_id,
                session_number=session_number,
                question=closing_message,
                question_count=question_count,
                survey_ended=True,
            )

        # Ask next question using previous responses
        question_count += 1
        await update_interaction(session_id, {"answers": answers, "question_count": question_count})

        question = await generate_question(request.campaign_id, session_id, answers)
        questions.append(question)
        await update_interaction(session_id, {"questions": questions})

        return SurveyResponse(
            session_id=session_id,
            session_number=session_number,
            question=question,
            question_count=question_count,
            survey_ended=False,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

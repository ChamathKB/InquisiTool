from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from inquisitool.agents.agents import generate_question
from inquisitool.db.mongodb import (
    create_interaction,
    get_interaction,
    update_interaction,
)
from inquisitool.utils import check_question_limit, end_survey

router = APIRouter()


class SurveyRequest(BaseModel):
    user_id: str
    session_id: str
    campaign_id: str
    answer: Optional[str] = None


class SurveyResponse(BaseModel):
    question: str
    question_count: int
    survey_ended: bool


@router.post("/survey", response_model=SurveyResponse)
async def process_survey(request: SurveyRequest):
    try:
        # Check if this is a new session (start) or existing (answer)
        try:
            interaction = await get_interaction(request.session_id)
            is_new = False
        except HTTPException:
            is_new = True

        if is_new:
            # Create new interaction
            interaction_data = {
                "campaign_id": request.campaign_id,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "answers": [],
                "questions": [],
                "question_count": 0,
                "survey_ended": False,
            }
            await create_interaction(interaction_data)
            question = await generate_question(campaign_id=request.campaign_id, responses=["/start"])
            await update_interaction(
                request.session_id,
                {
                    "questions": [question],
                    "question_count": 1,
                },
            )
            return SurveyResponse(question=question, question_count=1, survey_ended=False)

        # Handle answer
        answers = interaction.get("answers", [])
        answers.append(request.answer)
        questions = interaction.get("questions", [])
        question_count = len(questions)

        # Check if limit reached
        survey_ended = await check_question_limit(request.campaign_id, question_count)

        if survey_ended:
            await update_interaction(request.session_id, {"answers": answers, "survey_ended": True})
            await end_survey(request.session_id)
            return SurveyResponse(question="", question_count=question_count, survey_ended=True)

        # Ask next question using previous responses
        question = await generate_question(request.campaign_id, answers)
        questions.append(question)
        question_count += 1

        await update_interaction(
            request.session_id,
            {
                "answers": answers,
                "questions": questions,
                "question_count": question_count,
            },
        )

        return SurveyResponse(question=question, question_count=question_count, survey_ended=False)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

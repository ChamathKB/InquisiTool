# query_hit -> invoke_agent -> agentgenerating questions -> question count limit -> end_survey

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from inquisitool.agents.agents import ask, run_campaign
from inquisitool.db.mongodb import create_interaction, list_interactions
from inquisitool.utils import check_question_limit, end_survey

router = APIRouter()


class Query(BaseModel):
    query_text: str
    user_id: str
    session_id: str
    campaign_id: str


class QueryResponse(BaseModel):
    agent_response: str
    questions_generated: List[str]
    question_count: int
    survey_ended: bool


@router.post("/query", response_model=QueryResponse)
async def process_query(query: Query):
    try:
        # Invoke agent with query
        agent_response = ask(query.query_text)

        # Generate follow-up questions
        question = run_campaign(query.query_text)
        questions = [question] if isinstance(question, str) else question

        # Get existing interactions and append new questions
        existing_interactions = await list_interactions(query.campaign_id)
        all_questions = []
        for interaction in existing_interactions:
            all_questions.extend(interaction.get("questions_generated", []))
        all_questions.extend(questions)
        question_count = len(all_questions)

        # Check if question limit reached
        survey_complete = check_question_limit(campaign_id=query.campaign_id, question_count=question_count)

        # Store interaction data
        interaction_data = {
            "campaign_id": query.campaign_id,
            "user_id": query.user_id,
            "session_id": query.session_id,
            "query": query.query_text,
            "response": agent_response,
            "questions_generated": questions,
            "survey_ended": survey_complete,
        }
        await create_interaction(interaction_data)

        if survey_complete:
            await end_survey(query.session_id)

        return QueryResponse(
            agent_response=agent_response,
            questions_generated=questions,
            question_count=question_count,
            survey_ended=survey_complete,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/survey/{session_id}")
# async def get_survey_status(session_id: str):
#     try:
#         is_complete = check_question_limit(session_id)
#         return {"survey_complete": is_complete}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import SAMPLE_CAMPAIGN

SESSION_ID = "session-abc-123"

SAMPLE_INTERACTION = {
    "session_id": SESSION_ID,
    "session_number": 1,
    "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
    "campaign": SAMPLE_CAMPAIGN,
    "answers": [],
    "questions": ["What is your role?"],
    "question_count": 1,
    "survey_ended": False,
}


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@patch("inquisitool.routes.query.create_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.query.get_campaign", new_callable=AsyncMock)
@patch("inquisitool.routes.query.cache_get", new_callable=AsyncMock)
@patch("inquisitool.routes.query.cache_set", new_callable=AsyncMock)
@patch("inquisitool.routes.query.update_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.query.generate_question", return_value="What is your role?")
def test_new_survey_session(
    mock_gen, mock_update, mock_cache_set, mock_cache_get, mock_get_campaign, mock_create, client
):
    mock_cache_get.return_value = None
    mock_get_campaign.return_value = SAMPLE_CAMPAIGN
    mock_create.return_value = {"session_id": SESSION_ID, "session_number": 1}

    response = client.post(
        "/query/survey",
        json={
            "user_id": "user-1",
            "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == SESSION_ID
    assert data["survey_ended"] is False
    assert data["question"] == "What is your role?"


@patch("inquisitool.routes.query.get_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.query.cache_get", new_callable=AsyncMock)
@patch("inquisitool.routes.query.cache_set", new_callable=AsyncMock)
@patch("inquisitool.routes.query.update_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.query.generate_question", return_value="Follow-up question?")
def test_continue_survey_session(mock_gen, mock_update, mock_cache_set, mock_cache_get, mock_get_interaction, client):
    mock_cache_get.return_value = None
    mock_get_interaction.return_value = SAMPLE_INTERACTION

    response = client.post(
        "/query/survey",
        json={
            "user_id": "user-1",
            "session_id": SESSION_ID,
            "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
            "answer": "I am a developer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["survey_ended"] is False
    assert data["question"] == "Follow-up question?"


@patch("inquisitool.routes.query.get_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.query.cache_get", new_callable=AsyncMock)
@patch("inquisitool.routes.query.cache_delete", new_callable=AsyncMock)
@patch("inquisitool.routes.query.update_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.query.end_survey", new_callable=AsyncMock)
@patch("inquisitool.routes.query.generate_closing_message", return_value="Thank you!")
def test_survey_ends_at_question_limit(
    mock_closing, mock_end, mock_update, mock_cache_delete, mock_cache_get, mock_get_interaction, client
):
    exhausted = {**SAMPLE_INTERACTION, "questions": ["Q1", "Q2", "Q3"], "question_count": 3}
    mock_cache_get.return_value = None
    mock_get_interaction.return_value = exhausted

    response = client.post(
        "/query/survey",
        json={
            "user_id": "user-1",
            "session_id": SESSION_ID,
            "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
            "answer": "Final answer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["survey_ended"] is True
    assert data["question"] == "Thank you!"

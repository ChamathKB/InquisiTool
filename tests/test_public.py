from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import SAMPLE_CAMPAIGN

SESSION_ID = "pub-session-123"
API_KEY = "valid-api-key"
HEADERS = {"x-api-key": API_KEY}

SAMPLE_INTERACTION = {
    "session_id": SESSION_ID,
    "session_number": 1,
    "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
    "campaign": SAMPLE_CAMPAIGN,
    "answers": [],
    "questions": ["First question?"],
    "question_count": 1,
    "survey_ended": False,
}


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@patch("inquisitool.routes.public.create_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.update_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.generate_question", return_value="First question?")
@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_new_session(mock_resolve, mock_gen, mock_update, mock_create, client):
    mock_resolve.return_value = SAMPLE_CAMPAIGN
    mock_create.return_value = {"session_id": SESSION_ID, "session_number": 1}

    response = client.post(
        "/public/survey",
        json={"user_id": "ignored", "campaign_id": SAMPLE_CAMPAIGN["campaign_id"]},
        headers=HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == SESSION_ID
    assert data["survey_ended"] is False
    assert data["question"] == "First question?"


@patch("inquisitool.routes.public.get_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.cache_get", new_callable=AsyncMock)
@patch("inquisitool.routes.public.cache_set", new_callable=AsyncMock)
@patch("inquisitool.routes.public.update_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.generate_question", return_value="Next question?")
@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_continue_session(
    mock_resolve, mock_gen, mock_update, mock_cache_set, mock_cache_get, mock_get_interaction, client
):
    mock_resolve.return_value = SAMPLE_CAMPAIGN
    mock_cache_get.return_value = None
    mock_get_interaction.return_value = SAMPLE_INTERACTION

    response = client.post(
        "/public/survey",
        json={
            "user_id": "ignored",
            "session_id": SESSION_ID,
            "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
            "answer": "my answer",
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["survey_ended"] is False
    assert data["question"] == "Next question?"


@patch("inquisitool.routes.public.get_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.cache_get", new_callable=AsyncMock)
@patch("inquisitool.routes.public.cache_delete", new_callable=AsyncMock)
@patch("inquisitool.routes.public.update_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.end_survey", new_callable=AsyncMock)
@patch("inquisitool.routes.public.generate_closing_message", return_value="Thanks!")
@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_survey_ends_at_limit(
    mock_resolve, mock_closing, mock_end, mock_update, mock_cache_delete, mock_cache_get, mock_get_interaction, client
):
    mock_resolve.return_value = SAMPLE_CAMPAIGN
    mock_cache_get.return_value = None
    exhausted = {**SAMPLE_INTERACTION, "questions": ["Q1", "Q2", "Q3"], "question_count": 3}
    mock_get_interaction.return_value = exhausted

    response = client.post(
        "/public/survey",
        json={
            "user_id": "ignored",
            "session_id": SESSION_ID,
            "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
            "answer": "last answer",
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["survey_ended"] is True
    assert data["question"] == "Thanks!"


@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_invalid_api_key(mock_resolve, client):
    mock_resolve.side_effect = ValueError("Invalid API key")

    response = client.post(
        "/public/survey",
        json={"user_id": "u1", "campaign_id": SAMPLE_CAMPAIGN["campaign_id"]},
        headers={"x-api-key": "bad-key"},
    )

    assert response.status_code == 401


@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_origin_blocked(mock_resolve, client):
    mock_resolve.return_value = {**SAMPLE_CAMPAIGN, "allowed_origins": ["https://allowed.com"]}

    response = client.post(
        "/public/survey",
        json={"user_id": "u1", "campaign_id": SAMPLE_CAMPAIGN["campaign_id"]},
        headers={**HEADERS, "origin": "https://blocked.com"},
    )

    assert response.status_code == 403


@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_missing_api_key(mock_resolve, client):
    response = client.post(
        "/public/survey",
        json={"user_id": "u1", "campaign_id": SAMPLE_CAMPAIGN["campaign_id"]},
    )
    assert response.status_code == 422


@patch("inquisitool.routes.public.get_interaction", new_callable=AsyncMock)
@patch("inquisitool.routes.public.cache_get", new_callable=AsyncMock)
@patch("inquisitool.routes.public.get_campaign_by_api_key", new_callable=AsyncMock)
def test_public_session_not_found(mock_resolve, mock_cache_get, mock_get_interaction, client):
    mock_resolve.return_value = SAMPLE_CAMPAIGN
    mock_cache_get.return_value = None
    mock_get_interaction.side_effect = ValueError("Session not found")

    response = client.post(
        "/public/survey",
        json={
            "user_id": "u1",
            "session_id": "bad-session",
            "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
            "answer": "answer",
        },
        headers=HEADERS,
    )

    assert response.status_code == 404

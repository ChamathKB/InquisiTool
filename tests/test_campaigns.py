from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import SAMPLE_CAMPAIGN


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@patch("inquisitool.routes.campaigns.create_campaign", new_callable=AsyncMock)
@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_create_campaign(mock_get, mock_create, client):
    mock_create.return_value = {"campaign_id": SAMPLE_CAMPAIGN["campaign_id"]}
    mock_get.return_value = SAMPLE_CAMPAIGN

    payload = {
        k: SAMPLE_CAMPAIGN[k]
        for k in [
            "campaign_name",
            "campaign_description",
            "start_date",
            "end_date",
            "status",
            "target_audience",
            "number_of_questions",
            "collection_id",
        ]
    }
    response = client.post("/campaigns/campaigns/", json=payload)

    assert response.status_code == 200
    assert response.json()["campaign_name"] == "Test Campaign"


@patch("inquisitool.routes.campaigns.list_campaigns", new_callable=AsyncMock)
def test_list_campaigns(mock_list, client):
    mock_list.return_value = [SAMPLE_CAMPAIGN]
    response = client.get("/campaigns/campaigns/")
    assert response.status_code == 200
    assert len(response.json()) == 1


@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_get_campaign_not_found(mock_get, client):
    mock_get.side_effect = ValueError("Campaign not found")
    response = client.get("/campaigns/campaigns/nonexistent-id")
    assert response.status_code == 404


@patch("inquisitool.routes.campaigns.delete_campaign", new_callable=AsyncMock)
def test_delete_campaign(mock_delete, client):
    mock_delete.return_value = None
    response = client.delete(f"/campaigns/campaigns/{SAMPLE_CAMPAIGN['campaign_id']}")
    assert response.status_code == 200
    assert response.json()["message"] == "Campaign deleted successfully"


@patch("inquisitool.routes.campaigns.delete_campaign", new_callable=AsyncMock)
def test_delete_campaign_not_found(mock_delete, client):
    mock_delete.side_effect = ValueError("Campaign not found")
    response = client.delete("/campaigns/campaigns/nonexistent-id")
    assert response.status_code == 404


@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_get_campaign_success(mock_get, client):
    mock_get.return_value = SAMPLE_CAMPAIGN
    response = client.get(f"/campaigns/get_campaign/{SAMPLE_CAMPAIGN['campaign_id']}")
    assert response.status_code == 200
    assert response.json()["campaign_id"] == SAMPLE_CAMPAIGN["campaign_id"]


@patch("inquisitool.routes.campaigns.update_campaign", new_callable=AsyncMock)
@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_update_campaign_success(mock_get, mock_update, client):
    updated = {**SAMPLE_CAMPAIGN, "campaign_name": "Updated"}
    mock_get.return_value = updated
    response = client.put(
        f"/campaigns/update_campaign/{SAMPLE_CAMPAIGN['campaign_id']}",
        json={"campaign_name": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["campaign_name"] == "Updated"


@patch("inquisitool.routes.campaigns.update_campaign", new_callable=AsyncMock)
def test_update_campaign_not_found(mock_update, client):
    mock_update.side_effect = ValueError("Campaign not found")
    response = client.put("/campaigns/update_campaign/nonexistent-id", json={"campaign_name": "X"})
    assert response.status_code == 404


@patch("inquisitool.routes.campaigns.create_campaign", new_callable=AsyncMock)
def test_create_campaign_db_failure(mock_create, client):
    mock_create.side_effect = Exception("DB error")
    payload = {
        k: SAMPLE_CAMPAIGN[k]
        for k in [
            "campaign_name",
            "campaign_description",
            "start_date",
            "end_date",
            "status",
            "target_audience",
            "number_of_questions",
            "collection_id",
        ]
    }
    response = client.post("/campaigns/create_campaign", json=payload)
    assert response.status_code == 500


@patch("inquisitool.routes.campaigns.update_campaign", new_callable=AsyncMock)
@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_generate_api_key_success(mock_get, mock_update, client):
    mock_get.return_value = {**SAMPLE_CAMPAIGN, "api_key": "new-key"}
    response = client.post(f"/campaigns/{SAMPLE_CAMPAIGN['campaign_id']}/generate_key")
    assert response.status_code == 200
    assert response.json()["api_key"] == "new-key"


@patch("inquisitool.routes.campaigns.update_campaign", new_callable=AsyncMock)
def test_generate_api_key_not_found(mock_update, client):
    mock_update.side_effect = ValueError("Campaign not found")
    response = client.post("/campaigns/nonexistent-id/generate_key")
    assert response.status_code == 404


@patch("inquisitool.routes.campaigns.save_analysis", new_callable=AsyncMock)
@patch("inquisitool.routes.campaigns.analyze_campaign")
@patch("inquisitool.routes.campaigns.list_completed_interactions", new_callable=AsyncMock)
@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_analyze_campaign_success(mock_get, mock_list, mock_analyze, mock_save, client):
    mock_get.return_value = SAMPLE_CAMPAIGN
    mock_list.return_value = [{"session_id": "s1", "answers": ["a1"]}]
    mock_analyze.return_value = {
        "total_responses": 1,
        "question_summaries": [],
        "themes": ["theme1"],
        "sentiment": "positive",
        "insights": ["insight1"],
    }
    response = client.post(f"/campaigns/{SAMPLE_CAMPAIGN['campaign_id']}/analyze")
    assert response.status_code == 200
    assert response.json()["sentiment"] == "positive"


@patch("inquisitool.routes.campaigns.list_completed_interactions", new_callable=AsyncMock)
@patch("inquisitool.routes.campaigns.get_campaign", new_callable=AsyncMock)
def test_analyze_campaign_no_responses(mock_get, mock_list, client):
    mock_get.return_value = SAMPLE_CAMPAIGN
    mock_list.return_value = []
    response = client.post(f"/campaigns/{SAMPLE_CAMPAIGN['campaign_id']}/analyze")
    assert response.status_code == 422


@patch("inquisitool.routes.campaigns.get_analysis", new_callable=AsyncMock)
def test_get_analysis_success(mock_get_analysis, client):
    from datetime import datetime

    mock_get_analysis.return_value = {
        "campaign_id": SAMPLE_CAMPAIGN["campaign_id"],
        "total_responses": 2,
        "question_summaries": [],
        "themes": [],
        "sentiment": "neutral",
        "insights": [],
        "generated_at": datetime(2025, 1, 1).isoformat(),
    }
    response = client.get(f"/campaigns/{SAMPLE_CAMPAIGN['campaign_id']}/analysis")
    assert response.status_code == 200
    assert response.json()["sentiment"] == "neutral"


@patch("inquisitool.routes.campaigns.get_analysis", new_callable=AsyncMock)
def test_get_analysis_not_found(mock_get_analysis, client):
    mock_get_analysis.return_value = None
    response = client.get(f"/campaigns/{SAMPLE_CAMPAIGN['campaign_id']}/analysis")
    assert response.status_code == 404


@patch("inquisitool.routes.campaigns.chat_design")
def test_campaign_assist_in_progress(mock_chat, client):
    mock_chat.return_value = ("Tell me more about your goal.", False, None)
    response = client.post("/campaigns/assist", json={"message": "I want to survey developers", "history": []})
    assert response.status_code == 200
    data = response.json()
    assert data["is_complete"] is False
    assert data["config"] is None


@patch("inquisitool.routes.campaigns.chat_design")
def test_campaign_assist_complete(mock_chat, client):
    mock_chat.return_value = (
        "Here is your campaign config.",
        True,
        {
            "campaign_name": "Dev Survey",
            "campaign_description": "Survey for devs",
            "target_audience": "developers",
            "number_of_questions": 5,
            "branch_delta": 2,
            "status": "active",
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-12-31T00:00:00",
        },
    )
    response = client.post("/campaigns/assist", json={"message": "confirm", "history": []})
    assert response.status_code == 200
    data = response.json()
    assert data["is_complete"] is True
    assert data["config"]["campaign_name"] == "Dev Survey"

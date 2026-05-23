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

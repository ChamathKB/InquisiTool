from datetime import datetime

import pytest
from pydantic import ValidationError

from inquisitool.models.campaign import CampaignCreate, CampaignResponse
from inquisitool.models.interaction import SurveyRequest, SurveyResponse
from inquisitool.models.knowledgebase import KnowledgebaseCollectionResponse

NOW = datetime(2025, 1, 1, 0, 0, 0)
LATER = datetime(2025, 12, 31, 0, 0, 0)
CAMPAIGN_ID = "550e8400-e29b-41d4-a716-446655440000"

VALID_CAMPAIGN = {
    "campaign_name": "Test",
    "campaign_description": "Desc",
    "start_date": NOW,
    "end_date": LATER,
    "status": "active",
    "target_audience": "developers",
    "number_of_questions": 5,
    "collection_id": "col-1",
}


# ── CampaignCreate ────────────────────────────────────────────────────────────


def test_campaign_create_valid():
    c = CampaignCreate(**VALID_CAMPAIGN)
    assert c.campaign_name == "Test"
    assert c.number_of_questions == 5


@pytest.mark.parametrize("missing_field", VALID_CAMPAIGN.keys())
def test_campaign_create_missing_field(missing_field):
    data = {k: v for k, v in VALID_CAMPAIGN.items() if k != missing_field}
    with pytest.raises(ValidationError):
        CampaignCreate(**data)


def test_campaign_create_invalid_question_count():
    with pytest.raises(ValidationError):
        CampaignCreate(**{**VALID_CAMPAIGN, "number_of_questions": "not-a-number"})


# ── CampaignResponse ──────────────────────────────────────────────────────────


def test_campaign_response_valid():
    c = CampaignResponse(
        **VALID_CAMPAIGN,
        campaign_id=CAMPAIGN_ID,
        created_at=NOW,
        updated_at=NOW,
    )
    assert str(c.campaign_id) == CAMPAIGN_ID


def test_campaign_response_invalid_uuid():
    with pytest.raises(ValidationError):
        CampaignResponse(
            **VALID_CAMPAIGN,
            campaign_id="not-a-uuid",
            created_at=NOW,
            updated_at=NOW,
        )


# ── SurveyRequest ─────────────────────────────────────────────────────────────


def test_survey_request_new_session():
    r = SurveyRequest(user_id="u1", campaign_id="c1")
    assert r.session_id is None
    assert r.answer is None


def test_survey_request_existing_session():
    r = SurveyRequest(user_id="u1", campaign_id="c1", session_id="s1", answer="yes")
    assert r.session_id == "s1"
    assert r.answer == "yes"


def test_survey_request_missing_required():
    with pytest.raises(ValidationError):
        SurveyRequest(user_id="u1")  # missing campaign_id


# ── SurveyResponse ────────────────────────────────────────────────────────────


def test_survey_response_valid():
    r = SurveyResponse(
        session_id="s1",
        session_number=1,
        question="What is your role?",
        question_count=1,
        survey_ended=False,
    )
    assert r.survey_ended is False


def test_survey_response_missing_field():
    with pytest.raises(ValidationError):
        SurveyResponse(session_id="s1", session_number=1, question_count=1, survey_ended=False)


# ── KnowledgebaseCollectionResponse ──────────────────────────────────────────


def test_knowledgebase_response_valid():
    k = KnowledgebaseCollectionResponse(
        collection_id="col-1",
        collection_name="my_collection",
        uploaded_at=NOW,
    )
    assert k.collection_name == "my_collection"


def test_knowledgebase_response_invalid_date():
    with pytest.raises(ValidationError):
        KnowledgebaseCollectionResponse(
            collection_id="col-1",
            collection_name="my_collection",
            uploaded_at="not-a-date",
        )

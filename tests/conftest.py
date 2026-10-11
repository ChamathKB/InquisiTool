from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI

from inquisitool.routes import campaigns, knowledgebases, public, query


@pytest.fixture
def mock_redis():
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_qdrant():
    return MagicMock()


@pytest.fixture
def app(mock_redis, mock_qdrant):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.redis_client = mock_redis
        app.state.qdrant = mock_qdrant
        app.state.mongodb = AsyncMock()
        app.state.session = AsyncMock()
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(campaigns.router, prefix="/campaigns")
    app.include_router(knowledgebases.router, prefix="/knowledgebases")
    app.include_router(query.router, prefix="/query")
    app.include_router(public.router, prefix="/public")
    return app


SAMPLE_CAMPAIGN = {
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
    "campaign_name": "Test Campaign",
    "campaign_description": "A test campaign",
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-12-31T00:00:00",
    "status": "active",
    "target_audience": "developers",
    "number_of_questions": 3,
    "collection_id": "col-123",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
}

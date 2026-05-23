import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from inquisitool.db.redis import (
    cache_delete,
    cache_get,
    cache_set,
    campaign_key,
    embedding_cache_get,
    embedding_cache_set,
    embedding_key,
    interaction_key,
)


@pytest.mark.asyncio
async def test_cache_get_hit():
    client = AsyncMock()
    client.get = AsyncMock(return_value=json.dumps({"foo": "bar"}))
    result = await cache_get(client, "some-key")
    assert result == {"foo": "bar"}


@pytest.mark.asyncio
async def test_cache_get_miss():
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    result = await cache_get(client, "missing-key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set():
    client = AsyncMock()
    await cache_set(client, "key", {"a": 1}, ttl=60)
    client.set.assert_called_once_with("key", json.dumps({"a": 1}, default=str), ex=60)


@pytest.mark.asyncio
async def test_cache_delete():
    client = AsyncMock()
    await cache_delete(client, "key")
    client.delete.assert_called_once_with("key")


def test_key_helpers():
    assert campaign_key("c1") == "campaign:c1"
    assert interaction_key("s1") == "interaction:s1"
    assert embedding_key("hello") == f"embedding:{hash('hello')}"


@patch("inquisitool.db.redis.get_sync_client")
def test_embedding_cache_get_hit(mock_get_client):
    mock_client = MagicMock()
    mock_client.get.return_value = json.dumps([0.1, 0.2])
    mock_get_client.return_value = mock_client

    result = embedding_cache_get("text")
    assert result == [0.1, 0.2]


@patch("inquisitool.db.redis.get_sync_client")
def test_embedding_cache_get_miss(mock_get_client):
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_get_client.return_value = mock_client

    result = embedding_cache_get("text")
    assert result is None


@patch("inquisitool.db.redis.get_sync_client")
def test_embedding_cache_set(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    embedding_cache_set("text", [0.1, 0.2], ttl=100)
    mock_client.set.assert_called_once_with("text", json.dumps([0.1, 0.2]), ex=100)

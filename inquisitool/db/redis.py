import json
import logging

import redis
import redis.asyncio as aredis

from inquisitool.constants import REDIS_URL

logger = logging.getLogger(__name__)

_sync_client: redis.Redis | None = None


def get_sync_client() -> redis.Redis:
    global _sync_client
    if _sync_client is None:
        _sync_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _sync_client


async def cache_get(client: aredis.Redis, key: str) -> dict | None:
    data = await client.get(key)
    if data:
        logger.debug("cache hit: %s", key)
        return json.loads(data)
    logger.debug("cache miss: %s", key)
    return None


async def cache_set(client: aredis.Redis, key: str, value: dict, ttl: int = 3600) -> None:
    await client.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(client: aredis.Redis, key: str) -> None:
    await client.delete(key)


def embedding_cache_get(key: str) -> list[float] | None:
    data = get_sync_client().get(key)
    if data:
        logger.debug("cache hit: %s", key)
        return json.loads(data)
    logger.debug("cache miss: %s", key)
    return None


def embedding_cache_set(key: str, vector: list[float], ttl: int = 86400) -> None:
    get_sync_client().set(key, json.dumps(vector), ex=ttl)


def interaction_key(session_id: str) -> str:
    return f"interaction:{session_id}"


def campaign_key(campaign_id: str) -> str:
    return f"campaign:{campaign_id}"


def embedding_key(text: str) -> str:
    return f"embedding:{hash(text)}"

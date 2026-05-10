import json

import redis.asyncio as redis


async def cache_get(client: redis.Redis, key: str) -> dict | None:
    data = await client.get(key)
    return json.loads(data) if data else None


async def cache_set(client: redis.Redis, key: str, value: dict, ttl: int = 3600) -> None:
    await client.set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(client: redis.Redis, key: str) -> None:
    await client.delete(key)


def interaction_key(session_id: str) -> str:
    return f"interaction:{session_id}"


def campaign_key(campaign_id: str) -> str:
    return f"campaign:{campaign_id}"

"""Asyncio Redis repository, used by the LiveKit agent.

The agent runs inside an asyncio event loop that is also carrying real-time
audio, so it uses `redis.asyncio` rather than the blocking client: a stalled
Redis must not stall the voice pipeline.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from .keys import DEFAULT_SESSION_TTL_SECONDS, history_key, metadata_key

logger = logging.getLogger(__name__)


class AsyncRedisSessionRepository:
    """The subset of session state the agent touches: subject, turns, status."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> None:
        self.client = aioredis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    async def ping(self) -> bool:
        try:
            return bool(await self.client.ping())
        except RedisError as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False

    async def get_subject(self, session_id: str) -> str | None:
        """The subject the learner picked, written by the backend at token time."""
        try:
            return await self.client.hget(metadata_key(session_id), "subject")
        except RedisError as exc:
            logger.warning("Could not read subject for %s: %s", session_id, exc)
            return None

    async def append_turn(
        self,
        session_id: str,
        role: str,
        text: str,
        interrupted: bool = False,
        timestamp: float | None = None,
    ) -> dict[str, Any]:
        turn = {
            "role": role,
            "text": text,
            "interrupted": interrupted,
            "timestamp": timestamp if timestamp is not None else time.time(),
        }
        try:
            key = history_key(session_id)
            async with self.client.pipeline(transaction=False) as pipe:
                pipe.rpush(key, json.dumps(turn))
                pipe.expire(key, self.ttl_seconds)
                await pipe.execute()
        except RedisError as exc:
            logger.warning("Could not persist turn for %s: %s", session_id, exc)
        return turn

    async def get_history(self, session_id: str) -> list[dict[str, Any]]:
        try:
            raw_turns = await self.client.lrange(history_key(session_id), 0, -1)
        except RedisError as exc:
            logger.warning("Could not read history for %s: %s", session_id, exc)
            return []
        return [json.loads(turn) for turn in raw_turns]

    async def end_session(self, session_id: str) -> None:
        try:
            key = metadata_key(session_id)
            async with self.client.pipeline(transaction=False) as pipe:
                pipe.hset(key, mapping={"status": "ended", "ended_at": time.time()})
                pipe.expire(key, self.ttl_seconds)
                await pipe.execute()
        except RedisError as exc:
            logger.warning("Could not mark session %s ended: %s", session_id, exc)

    async def aclose(self) -> None:
        try:
            await self.client.aclose()
        except RedisError as exc:
            logger.warning("Error closing Redis connection: %s", exc)

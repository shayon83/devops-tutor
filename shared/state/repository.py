"""Synchronous Redis repository, used by the FastAPI backend."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from .keys import (
    DEFAULT_SESSION_TTL_SECONDS,
    feedback_key,
    history_key,
    metadata_key,
    user_sessions_key,
)

logger = logging.getLogger(__name__)

#: redis-py's default retry backs off for roughly ten seconds before giving
#: up. That is far too long to hold a voice turn (or an API request) open, so
#: retries are capped tightly: a healthy Redis never needs them, and an
#: unreachable one should be reported as degraded quickly.
_RETRY_POLICY = Retry(ExponentialBackoff(cap=0.2, base=0.02), retries=2)


class RedisSessionRepository:
    """Reads and writes tutoring-session state.

    Every method degrades gracefully when Redis is unreachable: a lesson that
    cannot be recorded should not take the API down. Only `RedisError` is
    caught -- a bug in this module still raises rather than being hidden
    behind a "Redis offline" warning.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        connect_timeout: float = 2.0,
        socket_timeout: float = 5.0,
    ) -> None:
        # Bounded timeouts: an unreachable or wedged Redis should degrade
        # quickly, not hold an API request (or a voice turn) open.
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            retry=_RETRY_POLICY,
        )
        self.ttl_seconds = ttl_seconds

    def ping(self) -> bool:
        """True when Redis answers. Used by the readiness probe."""
        try:
            return bool(self.client.ping())
        except RedisError as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False

    def create_session(
        self, session_id: str, user_id: str, subject: str = "DevOps"
    ) -> dict[str, Any]:
        now = time.time()
        metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "subject": subject,
            "summary": f"Discussion on {subject}",
            "created_at": now,
            "updated_at": now,
            "status": "active",
        }
        try:
            key = metadata_key(session_id)
            self.client.hset(key, mapping=metadata)
            self.client.expire(key, self.ttl_seconds)
            self.index_user_session(user_id, session_id, now)
        except RedisError as exc:
            logger.warning("Could not persist session metadata for %s: %s", session_id, exc)
        return metadata

    def index_user_session(
        self, user_id: str, session_id: str, timestamp: float | None = None
    ) -> None:
        if not user_id:
            return
        ts = timestamp if timestamp is not None else time.time()
        try:
            key = user_sessions_key(user_id)
            self.client.zadd(key, {session_id: ts})
            self.client.expire(key, self.ttl_seconds)
        except RedisError as exc:
            logger.warning("Could not index session for user %s: %s", user_id, exc)

    def get_user_sessions(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        if not user_id:
            return []
        try:
            key = user_sessions_key(user_id)
            session_ids = self.client.zrevrange(key, 0, limit - 1)
        except RedisError as exc:
            logger.warning("Could not read user sessions for %s: %s", user_id, exc)
            return []

        sessions = []
        for sid in session_ids:
            try:
                meta = dict(self.client.hgetall(metadata_key(sid)))
                if not meta:
                    continue
                turn_count = self.client.llen(history_key(sid))
                subj = meta.get("subject", "DevOps")
                summary = meta.get("summary", f"Discussion on {subj}")
                sessions.append({
                    "session_id": sid,
                    "user_id": meta.get("user_id", user_id),
                    "subject": subj,
                    "summary": summary,
                    "status": meta.get("status", "ended"),
                    "created_at": float(meta.get("created_at", 0)),
                    "updated_at": float(meta.get("updated_at", meta.get("created_at", 0))),
                    "turns_count": turn_count,
                })
            except RedisError as exc:
                logger.warning("Could not fetch details for session %s: %s", sid, exc)
        return sessions

    def update_summary(self, session_id: str, summary: str) -> None:
        now = time.time()
        try:
            key = metadata_key(session_id)
            self.client.hset(key, mapping={"summary": summary, "updated_at": now})
            self.client.expire(key, self.ttl_seconds)
            user_id = self.client.hget(key, "user_id")
            if user_id:
                self.index_user_session(user_id, session_id, now)
        except RedisError as exc:
            logger.warning("Could not update summary for %s: %s", session_id, exc)

    def reactivate_session(self, session_id: str) -> bool:
        try:
            key = metadata_key(session_id)
            if not self.client.exists(key):
                return False
            now = time.time()
            self.client.hset(key, mapping={"status": "active", "updated_at": now})
            self.client.expire(key, self.ttl_seconds)
            self.client.expire(history_key(session_id), self.ttl_seconds)
            user_id = self.client.hget(key, "user_id")
            if user_id:
                self.index_user_session(user_id, session_id, now)
            return True
        except RedisError as exc:
            logger.warning("Could not reactivate session %s: %s", session_id, exc)
            return False

    def get_metadata(self, session_id: str) -> dict[str, str]:
        try:
            return dict(self.client.hgetall(metadata_key(session_id)))
        except RedisError as exc:
            logger.warning("Could not read session metadata for %s: %s", session_id, exc)
            return {}

    def append_turn(
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
            self.client.rpush(key, json.dumps(turn))
            self.client.expire(key, self.ttl_seconds)
        except RedisError as exc:
            logger.warning("Could not persist turn for %s: %s", session_id, exc)
        return turn

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        try:
            raw_turns = self.client.lrange(history_key(session_id), 0, -1)
        except RedisError as exc:
            logger.warning("Could not read history for %s: %s", session_id, exc)
            return []
        return [json.loads(turn) for turn in raw_turns]

    def save_feedback(
        self,
        session_id: str,
        rating_stars: int,
        tags: list[str],
        comment: str | None = None,
    ) -> dict[str, Any]:
        feedback = {
            "rating_stars": rating_stars,
            "tags": json.dumps(tags),
            "comment": comment or "",
            "timestamp": time.time(),
        }
        try:
            key = feedback_key(session_id)
            self.client.hset(key, mapping=feedback)
            self.client.expire(key, self.ttl_seconds)
        except RedisError as exc:
            logger.warning("Could not persist feedback for %s: %s", session_id, exc)
        return feedback

    def end_session(self, session_id: str) -> None:
        try:
            key = metadata_key(session_id)
            self.client.hset(key, mapping={"status": "ended", "ended_at": time.time()})
            self.client.expire(key, self.ttl_seconds)
        except RedisError as exc:
            logger.warning("Could not mark session %s ended: %s", session_id, exc)

    def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """Session metadata, turns and feedback.

        Returns the same shape whether or not Redis is reachable, with
        `storage_available` saying which it was, so a Redis outage reads as an
        empty summary instead of a 500.
        """
        try:
            metadata = dict(self.client.hgetall(metadata_key(session_id)))
            raw_turns = self.client.lrange(history_key(session_id), 0, -1)
            feedback = dict(self.client.hgetall(feedback_key(session_id)))
        except RedisError as exc:
            logger.warning("Could not read summary for %s: %s", session_id, exc)
            return {
                "session_id": session_id,
                "metadata": {},
                "history": [],
                "feedback": {},
                "turns_count": 0,
                "storage_available": False,
            }

        history = [json.loads(turn) for turn in raw_turns]
        return {
            "session_id": session_id,
            "metadata": metadata,
            "history": history,
            "feedback": feedback,
            "turns_count": len(history),
            "storage_available": True,
        }

"""Round-trip tests for the shared Redis session store, against a real Redis."""

from __future__ import annotations

import json

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from shared.state import (
    AsyncRedisSessionRepository,
    RedisSessionRepository,
    feedback_key,
    history_key,
    metadata_key,
)

#: A port nothing listens on, to exercise the degraded paths for real.
DEAD_REDIS_PORT = 6399


def test_create_session_writes_metadata_with_a_ttl(redis_repository, session_id):
    redis_repository.create_session(session_id, user_id="student-42", subject="Kubernetes")

    stored = redis_repository.client.hgetall(metadata_key(session_id))
    assert stored["user_id"] == "student-42"
    assert stored["subject"] == "Kubernetes"
    assert stored["status"] == "active"
    assert redis_repository.client.ttl(metadata_key(session_id)) > 0


def test_turns_are_appended_in_order_and_read_back(redis_repository, session_id):
    redis_repository.append_turn(session_id, "user", "Why did my pod get OOMKilled?")
    redis_repository.append_turn(session_id, "assistant", "What memory limit did you set?")

    raw = redis_repository.client.lrange(history_key(session_id), 0, -1)
    assert [json.loads(turn)["role"] for turn in raw] == ["user", "assistant"]

    history = redis_repository.get_history(session_id)
    assert [turn["text"] for turn in history] == [
        "Why did my pod get OOMKilled?",
        "What memory limit did you set?",
    ]
    assert redis_repository.client.ttl(history_key(session_id)) > 0


def test_feedback_is_written_and_read_back(redis_repository, session_id):
    redis_repository.save_feedback(session_id, 5, ["clear_explanation"], "Great lesson")

    stored = redis_repository.client.hgetall(feedback_key(session_id))
    assert stored["rating_stars"] == "5"
    assert json.loads(stored["tags"]) == ["clear_explanation"]
    assert stored["comment"] == "Great lesson"


def test_end_session_marks_status_and_ended_at(redis_repository, session_id):
    redis_repository.create_session(session_id, user_id="student-1", subject="Linux")
    redis_repository.end_session(session_id)

    stored = redis_repository.client.hgetall(metadata_key(session_id))
    assert stored["status"] == "ended"
    assert float(stored["ended_at"]) > 0


def test_summary_reports_everything_that_was_written(redis_repository, session_id):
    redis_repository.create_session(session_id, user_id="student-7", subject="Terraform")
    redis_repository.append_turn(session_id, "user", "What is state locking?")
    redis_repository.save_feedback(session_id, 4, ["great_pacing"], None)

    summary = redis_repository.get_session_summary(session_id)
    assert summary["storage_available"] is True
    assert summary["metadata"]["subject"] == "Terraform"
    assert summary["turns_count"] == 1
    assert summary["history"][0]["text"] == "What is state locking?"
    assert summary["feedback"]["rating_stars"] == "4"


def test_summary_degrades_instead_of_raising_when_redis_is_down():
    offline = RedisSessionRepository(host="localhost", port=DEAD_REDIS_PORT, connect_timeout=0.25)

    summary = offline.get_session_summary("whatever")

    assert summary["storage_available"] is False
    assert summary["history"] == []
    assert summary["turns_count"] == 0
    assert offline.ping() is False


async def test_agent_reads_the_subject_the_backend_wrote(
    redis_repository, async_redis_repository, session_id
):
    """The subject picker only works if these two agree on the key layout."""
    redis_repository.create_session(session_id, user_id="student-9", subject="Observability")

    assert await async_redis_repository.get_subject(session_id) == "Observability"


async def test_agent_writes_turns_the_backend_can_read(
    redis_repository, async_redis_repository, session_id
):
    await async_redis_repository.append_turn(session_id, "user", "Explain SLOs.")
    await async_redis_repository.append_turn(
        session_id, "assistant", "What does your error budget allow?", interrupted=True
    )

    history = redis_repository.get_history(session_id)
    assert [(t["role"], t["interrupted"]) for t in history] == [
        ("user", False),
        ("assistant", True),
    ]
    assert redis_repository.client.ttl(history_key(session_id)) > 0


async def test_agent_end_session_is_visible_to_the_backend(
    redis_repository, async_redis_repository, session_id
):
    redis_repository.create_session(session_id, user_id="student-3", subject="CI/CD")

    await async_redis_repository.end_session(session_id)

    assert redis_repository.get_metadata(session_id)["status"] == "ended"


async def test_async_repository_degrades_when_redis_is_down():
    offline = AsyncRedisSessionRepository(
        host="localhost", port=DEAD_REDIS_PORT, connect_timeout=0.25
    )
    try:
        assert await offline.ping() is False
        assert await offline.get_subject("whatever") is None
        assert await offline.get_history("whatever") == []
    finally:
        await offline.aclose()


def test_connection_errors_are_absorbed_but_bugs_are_not(redis_repository, monkeypatch):
    """Only RedisError is caught, so a bug here cannot look like an outage."""
    monkeypatch.setattr(
        redis_repository.client,
        "hset",
        lambda *a, **k: (_ for _ in ()).throw(RedisConnectionError("redis is down")),
    )
    # A real outage degrades quietly and still returns the turn it tried to write.
    assert redis_repository.create_session("sid", "student", "Linux")["status"] == "active"

    monkeypatch.setattr(
        redis_repository.client,
        "hset",
        lambda *a, **k: (_ for _ in ()).throw(TypeError("wrong argument type")),
    )
    with pytest.raises(TypeError):
        redis_repository.create_session("sid", "student", "Linux")

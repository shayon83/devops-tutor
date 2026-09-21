"""Root fixtures: dummy LiveKit credentials and a real Redis.

The suites deliberately talk to a real Redis rather than a stub. Redis is the
conversation store the assignment requires, so "did the turn actually land in
`session:<room>:history`?" is the thing worth asserting -- and the previous
tests passed with Redis stopped, because every error was swallowed.
"""

from __future__ import annotations

import os
import uuid

import pytest

# Set before any test module imports `backend.src.config`, which reads these at
# import time and refuses to start without them.
os.environ.setdefault("LIVEKIT_URL", "wss://ci-dummy.livekit.cloud")
os.environ.setdefault("LIVEKIT_API_KEY", "ci-dummy-api-key")
os.environ.setdefault("LIVEKIT_API_SECRET", "ci-dummy-api-secret-at-least-32-bytes-long")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://localhost:3000")

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])


@pytest.fixture(scope="session")
def redis_repository():
    from shared.state import RedisSessionRepository

    repository = RedisSessionRepository(host=REDIS_HOST, port=REDIS_PORT)
    if not repository.ping():
        # Fail, never skip: a skipped store test tells you nothing.
        pytest.fail(
            f"These tests need a running Redis at {REDIS_HOST}:{REDIS_PORT}. "
            "Start one with `docker compose up -d redis`."
        )
    return repository


@pytest.fixture
async def async_redis_repository():
    from shared.state import AsyncRedisSessionRepository

    repository = AsyncRedisSessionRepository(host=REDIS_HOST, port=REDIS_PORT)
    if not await repository.ping():
        pytest.fail(f"These tests need a running Redis at {REDIS_HOST}:{REDIS_PORT}.")
    try:
        yield repository
    finally:
        await repository.aclose()


@pytest.fixture
def session_id(redis_repository):
    """A unique session id, with its keys removed afterwards."""
    from shared.state import feedback_key, history_key, metadata_key

    sid = f"test-room-{uuid.uuid4().hex[:10]}"
    yield sid
    redis_repository.client.delete(metadata_key(sid), history_key(sid), feedback_key(sid))

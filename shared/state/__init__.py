"""Shared Redis conversation store.

The backend and the agent are separate images, but they read and write the
same `session:<room>:*` keys. That key layout is a contract between them, so
it lives here once and both images copy this package, rather than the agent
importing `backend.src.*` (which coupled the two services) or keeping a second
copy that can drift.
"""

from .async_repository import AsyncRedisSessionRepository
from .keys import DEFAULT_SESSION_TTL_SECONDS, feedback_key, history_key, metadata_key
from .repository import RedisSessionRepository

__all__ = [
    "AsyncRedisSessionRepository",
    "RedisSessionRepository",
    "DEFAULT_SESSION_TTL_SECONDS",
    "feedback_key",
    "history_key",
    "metadata_key",
]

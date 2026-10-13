"""Key layout and TTL for tutoring-session state in Redis."""

from __future__ import annotations

import os

#: Sessions are a transcript of one lesson, not a system of record, so they
#: expire rather than growing without bound.
DEFAULT_SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "86400"))


def metadata_key(session_id: str) -> str:
    """Hash of session metadata: user, subject, status, timestamps."""
    return f"session:{session_id}:metadata"


def history_key(session_id: str) -> str:
    """List of JSON-encoded conversation turns, oldest first."""
    return f"session:{session_id}:history"


def feedback_key(session_id: str) -> str:
    """Hash of the post-session CSAT rating, tags and comment."""
    return f"session:{session_id}:feedback"


def user_sessions_key(user_id: str) -> str:
    """Sorted set of session IDs for a user, scored by last updated timestamp."""
    return f"user:{user_id}:sessions"


def extract_session_id(room_name: str) -> str:
    """Extracts canonical session ID from a room name (e.g. 'sess-123--call-456' -> 'sess-123')."""
    return room_name.split("--")[0] if room_name else ""


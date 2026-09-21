"""Shared fixtures for the agent test suite."""

from __future__ import annotations

import pytest

#: The previous suite skipped whenever LIVEKIT_API_KEY was unset, so in CI it
#: always skipped and could never catch a bad model ID or a changed SDK API.
#: Dummy credentials are enough to construct the agent (nothing dials out), so
#: the tests below genuinely run -- and genuinely fail.
DUMMY_LIVEKIT_ENV = {
    "LIVEKIT_URL": "wss://ci-dummy.livekit.cloud",
    "LIVEKIT_API_KEY": "ci-dummy-api-key",
    "LIVEKIT_API_SECRET": "ci-dummy-api-secret-at-least-32-bytes-long",
}


@pytest.fixture(autouse=True)
def dummy_livekit_credentials(monkeypatch):
    for key, value in DUMMY_LIVEKIT_ENV.items():
        monkeypatch.setenv(key, value)
    # Model IDs must come from the factory defaults unless a test says otherwise.
    for key in ("STT_MODEL", "LLM_MODEL", "TTS_MODEL"):
        monkeypatch.delenv(key, raising=False)

"""Backend configuration, read entirely from the environment (`.env`)."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

#: Values shipped in `.env.example` as placeholders. Starting with one of these
#: still set means the operator never filled `.env` in, which is a
#: misconfiguration worth failing on rather than issuing unusable tokens.
_PLACEHOLDERS = {
    "your_livekit_api_key",
    "your_livekit_api_secret",
    "wss://your-livekit-server.livekit.cloud",
}


class ConfigurationError(RuntimeError):
    """Raised at import time when required configuration is missing."""


class Settings(BaseModel):
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    redis_host: str
    redis_port: int
    cors_allow_origins: list[str]


def _required(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise ConfigurationError(
            f"{name} is not set. Copy .env.example to .env and fill in your "
            f"LiveKit Cloud credentials (https://cloud.livekit.io)."
        )
    if value in _PLACEHOLDERS:
        raise ConfigurationError(
            f"{name} is still set to the .env.example placeholder {value!r}. "
            f"Replace it with a real value."
        )
    return value


def load_settings() -> Settings:
    return Settings(
        livekit_url=_required("LIVEKIT_URL"),
        livekit_api_key=_required("LIVEKIT_API_KEY"),
        livekit_api_secret=_required("LIVEKIT_API_SECRET"),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        # Only the frontend origin, not "*". Override when serving the SPA
        # from somewhere other than http://localhost:3000.
        cors_allow_origins=[
            origin.strip()
            for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ],
    )


settings = load_settings()

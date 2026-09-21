"""FastAPI backend: LiveKit access tokens and session state.

The token endpoint is deliberately unauthenticated -- this is a demo, and the
walkthrough should work from a fresh clone with no sign-up. See the README for
what would have to change before it faced real users.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from backend.src.config import settings
from shared.state import RedisSessionRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="DevOps Voice Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

redis_repo = RedisSessionRepository(host=settings.redis_host, port=settings.redis_port)

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "handler", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "handler"]
)
# A Histogram, not a per-session Gauge: labelling by session_id gave every
# session its own time series, which is unbounded cardinality.
CSAT_RATING = Histogram(
    "voice_tutor_csat_rating_stars",
    "Learner CSAT star rating",
    buckets=[1, 2, 3, 4, 5],
)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    """Instruments every route, not just the two that used to do it by hand."""
    start = time.perf_counter()
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        # Read the route *after* routing: it is the path template
        # ("/api/session/{session_id}/feedback"), so path parameters do not
        # explode the label cardinality. Unmatched paths share one label so an
        # unrouted request cannot mint a new time series either.
        route = request.scope.get("route")
        handler = getattr(route, "path", None) or "<unmatched>"
        REQUEST_COUNT.labels(method=request.method, handler=handler, status=status).inc()
        REQUEST_LATENCY.labels(method=request.method, handler=handler).observe(
            time.perf_counter() - start
        )


class TokenRequest(BaseModel):
    # The room name and participant identity are generated server-side, so a
    # client cannot name (or join) an arbitrary room.
    subject: str = Field(default="DevOps", min_length=1, max_length=80)


class TokenResponse(BaseModel):
    token: str
    livekit_url: str
    room_name: str
    participant_identity: str


class FeedbackRequest(BaseModel):
    rating_stars: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=10)
    comment: str | None = Field(default=None, max_length=2000)


@app.get("/health")
def health_check():
    """Liveness: the process is up. Says nothing about its dependencies."""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/ready")
def readiness_check(response: Response):
    """Readiness: Redis answers, so a session can actually be recorded."""
    redis_ok = redis_repo.ping()
    if not redis_ok:
        response.status_code = 503
    return {"status": "ready" if redis_ok else "degraded", "redis": redis_ok}


@app.post("/api/token", response_model=TokenResponse)
def generate_livekit_token(req: TokenRequest):
    room_name = f"devops-room-{uuid.uuid4().hex[:12]}"
    participant_identity = f"student-{uuid.uuid4().hex[:8]}"

    try:
        token = (
            api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity(participant_identity)
            .with_name(participant_identity)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
        )
        jwt_token = token.to_jwt()
    except Exception as exc:
        logger.error("Error generating token: %s", exc)
        raise HTTPException(status_code=500, detail="Could not issue a LiveKit token") from exc

    # The agent reads `subject` back out of this hash when the job starts.
    redis_repo.create_session(
        session_id=room_name, user_id=participant_identity, subject=req.subject
    )

    return TokenResponse(
        token=jwt_token,
        livekit_url=settings.livekit_url,
        room_name=room_name,
        participant_identity=participant_identity,
    )


@app.get("/api/session/{session_id}")
def get_session_summary(session_id: str):
    return redis_repo.get_session_summary(session_id)


@app.post("/api/session/{session_id}/feedback")
def submit_feedback(session_id: str, req: FeedbackRequest):
    result = redis_repo.save_feedback(session_id, req.rating_stars, req.tags, req.comment)
    CSAT_RATING.observe(req.rating_stars)
    return {"status": "success", "feedback": result}


@app.get("/metrics")
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

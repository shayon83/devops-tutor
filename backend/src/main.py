import time
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from livekit import api

from backend.src.config import settings
from backend.src.session_manager import RedisSessionRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="DevOps Voice Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_repo = RedisSessionRepository(host=settings.redis_host, port=settings.redis_port)

# Prometheus Metrics Instrumentation
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "handler", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Duration", ["method", "handler"])
CSAT_RATING_GAUGE = Gauge("voice_tutor_csat_rating_stars", "Learner CSAT Star Rating", ["session_id"])
ACTIVE_SESSIONS_GAUGE = Gauge("voice_tutor_active_sessions_total", "Active Voice Sessions Count")

class TokenRequest(BaseModel):
    room_name: str
    participant_identity: str
    subject: Optional[str] = "DevOps"

class TokenResponse(BaseModel):
    token: str
    livekit_url: str
    room_name: str
    participant_identity: str

class FeedbackRequest(BaseModel):
    rating_stars: int
    tags: List[str] = []
    comment: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/api/token", response_model=TokenResponse)
def generate_livekit_token(req: TokenRequest):
    start_time = time.time()
    try:
        api_key = settings.livekit_api_key or "devkey"
        api_secret = settings.livekit_api_secret or "secretsecretsecretsecretsecretsecret"

        token = api.AccessToken(api_key, api_secret) \
            .with_identity(req.participant_identity) \
            .with_name(req.participant_identity) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=req.room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            ))

        jwt_token = token.to_jwt()
        redis_repo.create_session(session_id=req.room_name, user_id=req.participant_identity, subject=req.subject or "DevOps")
        ACTIVE_SESSIONS_GAUGE.inc()
        REQUEST_COUNT.labels(method="POST", handler="/api/token", status="200").inc()
        REQUEST_LATENCY.labels(method="POST", handler="/api/token").observe(time.time() - start_time)

        return TokenResponse(
            token=jwt_token,
            livekit_url=settings.livekit_url,
            room_name=req.room_name,
            participant_identity=req.participant_identity
        )
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        REQUEST_COUNT.labels(method="POST", handler="/api/token", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
def get_session_summary(session_id: str):
    return redis_repo.get_session_summary(session_id)

@app.post("/api/session/{session_id}/feedback")
def submit_feedback(session_id: str, req: FeedbackRequest):
    if req.rating_stars < 1 or req.rating_stars > 5:
        raise HTTPException(status_code=400, detail="Rating stars must be between 1 and 5")
    
    result = redis_repo.save_feedback(session_id, req.rating_stars, req.tags, req.comment)
    CSAT_RATING_GAUGE.labels(session_id=session_id).set(req.rating_stars)
    REQUEST_COUNT.labels(method="POST", handler="/api/session/feedback", status="200").inc()
    return {"status": "success", "feedback": result}

@app.get("/metrics")
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

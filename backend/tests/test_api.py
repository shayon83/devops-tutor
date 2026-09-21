"""Backend API tests. These run against a real Redis (see the root conftest)."""

from __future__ import annotations

import json
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from backend.src import main as backend_main
from backend.src.config import ConfigurationError, _required
from backend.src.main import app
from shared.state import feedback_key, history_key, metadata_key


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def issued_session(client, redis_repository):
    """A session created the way the frontend creates one, cleaned up after."""
    response = client.post("/api/token", json={"subject": "Kubernetes & Container Orchestration"})
    assert response.status_code == 200
    body = response.json()
    yield body
    room = body["room_name"]
    redis_repository.client.delete(metadata_key(room), history_key(room), feedback_key(room))


def test_health_is_liveness_only(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_reports_that_redis_answers(client, redis_repository):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "redis": True}


def test_token_is_a_signed_jwt_for_a_server_generated_room(issued_session):
    assert issued_session["room_name"].startswith("devops-room-")
    assert issued_session["participant_identity"].startswith("student-")

    claims = jwt.decode(
        issued_session["token"],
        "ci-dummy-api-secret-at-least-32-bytes-long",
        algorithms=["HS256"],
        options={"verify_aud": False},
    )
    assert claims["sub"] == issued_session["participant_identity"]
    assert claims["video"]["room"] == issued_session["room_name"]
    assert claims["video"]["roomJoin"] is True


def test_token_endpoint_writes_session_metadata_to_redis(issued_session, redis_repository):
    stored = redis_repository.client.hgetall(metadata_key(issued_session["room_name"]))

    assert stored["subject"] == "Kubernetes & Container Orchestration"
    assert stored["user_id"] == issued_session["participant_identity"]
    assert stored["status"] == "active"
    assert redis_repository.client.ttl(metadata_key(issued_session["room_name"])) > 0


def test_client_cannot_choose_its_own_room(client, redis_repository):
    response = client.post(
        "/api/token",
        json={
            "subject": "Linux",
            "room_name": "someone-elses-room",
            "participant_identity": "admin",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["room_name"] != "someone-elses-room"
    assert body["participant_identity"] != "admin"
    redis_repository.client.delete(metadata_key(body["room_name"]))


def test_subject_is_rejected_when_empty_or_too_long(client):
    assert client.post("/api/token", json={"subject": ""}).status_code == 422
    assert client.post("/api/token", json={"subject": "x" * 81}).status_code == 422


def test_feedback_is_stored_and_visible_in_the_summary(client, issued_session, redis_repository):
    room = issued_session["room_name"]
    redis_repository.append_turn(room, "user", "What is a readiness probe?")

    response = client.post(
        f"/api/session/{room}/feedback",
        json={"rating_stars": 5, "tags": ["clear_explanation"], "comment": "Great lesson"},
    )
    assert response.status_code == 200

    stored = redis_repository.client.hgetall(feedback_key(room))
    assert stored["rating_stars"] == "5"
    assert json.loads(stored["tags"]) == ["clear_explanation"]

    summary = client.get(f"/api/session/{room}").json()
    assert summary["storage_available"] is True
    assert summary["metadata"]["subject"] == "Kubernetes & Container Orchestration"
    assert summary["turns_count"] == 1
    assert summary["history"][0]["text"] == "What is a readiness probe?"
    assert summary["feedback"]["comment"] == "Great lesson"


def test_feedback_rejects_an_out_of_range_rating(client, issued_session):
    response = client.post(
        f"/api/session/{issued_session['room_name']}/feedback",
        json={"rating_stars": 6, "tags": []},
    )
    assert response.status_code == 422


def test_summary_of_an_unknown_session_is_empty_not_an_error(client):
    summary = client.get("/api/session/never-existed").json()
    assert summary["metadata"] == {}
    assert summary["history"] == []
    assert summary["storage_available"] is True


def test_cors_is_limited_to_the_configured_frontend_origin(client):
    allowed = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"

    denied = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in denied.headers


def test_metrics_cover_every_route_not_just_two(client, issued_session):
    client.get("/health")
    body = client.get("/metrics").text

    assert 'handler="/health"' in body
    assert 'handler="/api/token"' in body
    assert "voice_tutor_csat_rating_stars_bucket" in body
    # The per-session CSAT gauge is gone: one time series per session was
    # unbounded cardinality.
    assert 'voice_tutor_csat_rating_stars{session_id=' not in body


def test_backend_no_longer_owns_the_active_sessions_gauge():
    """Issuing a token is not an active session; the agent owns that gauge.

    Asserted against the source rather than /metrics: the agent's metrics
    module registers the gauge in the same default registry when both suites
    run in one pytest process.
    """
    source = Path(backend_main.__file__).read_text()
    assert "voice_tutor_active_sessions_total" not in source
    assert "from prometheus_client import" in source
    assert "Gauge," not in source


@pytest.mark.parametrize(
    "value",
    ["", "   ", "your_livekit_api_key"],
)
def test_startup_fails_fast_on_missing_or_placeholder_credentials(monkeypatch, value):
    monkeypatch.setenv("LIVEKIT_API_KEY", value)
    with pytest.raises(ConfigurationError):
        _required("LIVEKIT_API_KEY")

from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generate_token_success():
    payload = {
        "room_name": "test-room-101",
        "participant_identity": "test-student-1",
        "subject": "DevOps"
    }
    response = client.post("/api/token", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["room_name"] == "test-room-101"
    assert data["participant_identity"] == "test-student-1"

def test_submit_feedback_success():
    payload = {
        "rating_stars": 5,
        "tags": ["clear_explanation", "great_pacing"],
        "comment": "Awesome DevOps voice tutor lesson!"
    }
    response = client.post("/api/session/test-room-101/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_submit_feedback_invalid_rating():
    payload = {
        "rating_stars": 6,
        "tags": []
    }
    response = client.post("/api/session/test-room-101/feedback", json=payload)
    assert response.status_code == 400

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.content

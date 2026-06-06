import sys
from pathlib import Path
import pytest
import jwt

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_login(client):
    response = client.post("/login", json={"username": "alice", "role": "student"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Decode and verify token
    token = data["access_token"]
    payload = jwt.decode(token, "b-learn-super-secret-key-1015", algorithms=["HS256"])
    assert payload["sub"] == "alice"
    assert payload["role"] == "student"

def test_recommendations_unauthorized(client):
    response = client.get("/recommendations/stud_1")
    assert response.status_code == 401

def test_recommendations_not_found(client, auth_headers):
    response = client.get("/recommendations/unknown_student", headers=auth_headers)
    assert response.status_code == 404

def test_recommendations_success(client, auth_headers):
    response = client.get("/recommendations/stud_1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id_hash"] == "stud_1"
    assert data["served_by"] == "FastAPI Gateway"
    assert "dropout_probability" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert "bkt_mastery" in data

def test_track_click(client, auth_headers):
    payload = {
        "student_id_hash": "stud_1",
        "id_site": 101,
        "code_module": "AAA",
        "code_presentation": "2014J",
        "sum_click": 5,
        "event_type": "click",
        "page_path": "/course/material",
        "source": "frontend-demo"
    }
    response = client.post("/track-click", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is True
    assert data["queued"] is True
    assert "event_time" in data

def test_submit_assessment_bkt_updates(client, auth_headers):
    # Fetch initial recommendations to check baseline BKT
    resp_init = client.get("/recommendations/stud_1", headers=auth_headers)
    init_bkt = resp_init.json()["bkt_mastery"]["C1"]

    # Submit assessment with 100% score (this should increase mastery)
    submit_payload = {
        "student_id_hash": "stud_1",
        "assignment_id": "546803",  # Maps to C1
        "score": 100.0
    }
    response = client.post("/submit-assessment", json=submit_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Fetch recommendations again to verify BKT mastery increased
    resp_after = client.get("/recommendations/stud_1", headers=auth_headers)
    after_bkt = resp_after.json()["bkt_mastery"]["C1"]
    assert after_bkt > init_bkt

def test_reset_assessment_shifts(client, auth_headers):
    response = client.post("/reset-assessment-shifts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

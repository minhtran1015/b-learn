import sys
import os
import importlib.util
from pathlib import Path

# Resolve repository root and add to sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Dynamically import backend-api/serving_gateway.py due to hyphen in folder name
gateway_path = REPO_ROOT / "backend-api" / "serving_gateway.py"
spec = importlib.util.spec_from_file_location("serving_gateway", str(gateway_path))
serving_gateway = importlib.util.module_from_spec(spec)
sys.modules["backend_api_serving_gateway"] = serving_gateway
spec.loader.exec_module(serving_gateway)

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "b-learn-super-secret-key-1015")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "mockaccount")
    monkeypatch.setenv("AZURE_STORAGE_KEY", "")
    monkeypatch.setenv("CLICK_FALLBACK_LOG_PATH", "/tmp/fallback_clicks_test.log")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

@pytest.fixture(autouse=True)
def mock_serving_io(monkeypatch):
    mock_user_emb = pd.DataFrame([
        {"student_id_hash": "stud_1", "user_embedding": [0.1, 0.2, 0.3]},
        {"student_id_hash": "stud_2", "user_embedding": [0.4, 0.5, 0.6]}
    ])
    mock_item_emb = pd.DataFrame([
        {"id_site": 101, "item_embedding": [0.1, 0.2, 0.3]},
        {"id_site": 102, "item_embedding": [0.2, 0.3, 0.4]},
        {"id_site": 103, "item_embedding": [0.3, 0.4, 0.5]}
    ])
    mock_risk = pd.DataFrame([
        {"student_id_hash": "stud_1", "dropout_probability": 0.15},
        {"student_id_hash": "stud_2", "dropout_probability": 0.85}
    ])
    mock_risk_features = pd.DataFrame([
        {
            "student_id_hash": "stud_1",
            "code_module": "AAA",
            "code_presentation": "2014J",
            "gender": "M",
            "region": "North",
            "highest_education": "A Level",
            "imd_band": "50-60%",
            "age_band": "0-35",
            "num_of_prev_attempts": 0.0,
            "studied_credits": 60.0,
            "disability": "N",
            "total_clicks": 150.0,
            "active_days": 10.0,
            "avg_daily_clicks": 15.0,
            "max_clicks_day": 30.0,
            "engagement_span": 20.0,
            "recent_weekly_rate": 5.0,
            "recency_days": 2.0,
            "engagement_momentum": 2.0,
            "avg_score": 75.0,
            "min_score": 60.0,
            "submission_count": 2.0,
            "late_submissions": 0.0,
            "weighted_avg": 75.0
        }
    ])
    mock_bkt = pd.DataFrame([
        {"user_id": "stud_1", "skill_name": "AAA_C1", "state_predictions": 0.65}
    ])
    mock_lms = pd.DataFrame([
        {"id_site": 101, "title": "Lecture 1", "type": "video", "chapter": "C1", "status": "Mở khóa"},
        {"id_site": 102, "title": "Reading 1", "type": "pdf", "chapter": "C1", "status": "Mở khóa"},
        {"id_site": 103, "title": "Quiz 1", "type": "quiz", "chapter": "C2", "status": "Khóa"}
    ])

    def mock_load_parquet_file(file_name: str) -> pd.DataFrame:
        if file_name == "user_embeddings.parquet":
            return mock_user_emb
        elif file_name == "item_embeddings.parquet":
            return mock_item_emb
        elif file_name == "risk_predictions.parquet":
            return mock_risk
        elif file_name == "risk_features.parquet":
            return mock_risk_features
        elif file_name == "bkt_mastery.parquet":
            return mock_bkt
        elif file_name == "lms_simulator.parquet":
            return mock_lms
        raise FileNotFoundError(f"Mock file not found: {file_name}")

    monkeypatch.setattr(serving_gateway, "load_parquet_file", mock_load_parquet_file)
    
    # Mock load_lgbm_model to avoid model load latency/errors
    monkeypatch.setattr(serving_gateway, "load_lgbm_model", lambda: None)
    
    # Mock KafkaProducer provider to raise immediate error so it falls back to log writing
    def mock_get_click_producer():
        raise ConnectionError("Mocked Kafka bootstrap connection failure")
    monkeypatch.setattr(serving_gateway, "_get_click_producer", mock_get_click_producer)

    # Ensure cache is pre-warmed using mock files
    serving_gateway.last_loaded = None
    serving_gateway.get_cached_data()

@pytest.fixture
def client():
    return TestClient(serving_gateway.app)

@pytest.fixture
def auth_headers(client):
    response = client.post("/login", json={"username": "test_user", "role": "student"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

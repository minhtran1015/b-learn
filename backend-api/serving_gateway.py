import os
import sys
import json
import jwt
import datetime
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import pandas as pd
import numpy as np
from azure.storage.blob import ContainerClient
import io
import joblib
from kafka import KafkaProducer
import redis
import threading

# Resolve repository root and add to sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

class SharedCache:
    _lock = threading.Lock()
    
    def __init__(self, host="localhost", port=6379, db=0, fallback_path="/tmp/b_learn_shared_state.json"):
        self.fallback_path = fallback_path
        self.redis_client = None
        try:
            # Short timeout to avoid hanging startup if Redis is not running
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                socket_timeout=1.0, 
                socket_connect_timeout=1.0
            )
            self.redis_client.ping()
            print("Connected to Redis successfully for shared state cache.")
        except Exception as e:
            print(f"Redis not available ({e}). Falling back to local file-based shared cache: {fallback_path}")
            self.redis_client = None

    def _read_fallback(self) -> dict:
        with self._lock:
            if not os.path.exists(self.fallback_path):
                return {}
            try:
                with open(self.fallback_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
            except Exception as e:
                print(f"Error reading shared cache file fallback: {e}")
                return {}

    def _write_fallback(self, data: dict):
        with self._lock:
            try:
                temp_path = self.fallback_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(temp_path, self.fallback_path)
            except Exception as e:
                print(f"Error writing shared cache file fallback: {e}")

    def get(self, key: str, default=None):
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                if val is not None:
                    return json.loads(val)
            except Exception as e:
                print(f"Redis read error for key {key}: {e}, falling back to file cache")
        
        data = self._read_fallback()
        return data.get(key, default)

    def set(self, key: str, value):
        if self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(value, ensure_ascii=False))
                return
            except Exception as e:
                print(f"Redis write error for key {key}: {e}, falling back to file cache")
        
        data = self._read_fallback()
        data[key] = value
        self._write_fallback(data)

    def clear(self):
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"Redis clear error: {e}")
        self._write_fallback({})


app = FastAPI(
    title="B-Learn Serving Gateway",
    description="FastAPI High-Speed Recommendation Serving Gateway with JWT security",
    version="1.0.0"
)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "b-learn-super-secret-key-1015")
ALGORITHM = "HS256"
ALLOWED_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    print("Pre-warming data cache...")
    try:
        get_cached_data()
        print("Data cache pre-warmed successfully.")
    except Exception as e:
        print(f"Warning: Data cache pre-warming failed: {e}")

storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

# Cache dữ liệu trong bộ nhớ để tránh I/O mạng liên tục
df_user_emb = None
df_item_emb = None
df_risk = None
df_lms_meta = None
df_risk_features = None
df_bkt_mastery = None
last_loaded = None
click_producer = None

# Fast lookup caches
_user_emb_dict = {}       # student_id_hash -> numpy array
_item_emb_matrix = None   # stacked numpy array of shape [num_items, emb_dim]
_item_ids_list = []       # list of item ids corresponding to rows in _item_emb_matrix
_student_risk_dict = {}   # student_id_hash -> dropout_probability
_lms_by_site_cache = {}   # id_site -> dict

shared_cache = SharedCache(host=os.getenv("REDIS_HOST", "localhost"))

GOLD_FEATURE_COLUMNS = [
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "num_of_prev_attempts",
    "studied_credits",
    "disability",
    "total_clicks",
    "active_days",
    "avg_daily_clicks",
    "max_clicks_day",
    "engagement_span",
    "recent_weekly_rate",
    "recency_days",
    "engagement_momentum",
    "avg_score",
    "min_score",
    "submission_count",
    "late_submissions",
    "weighted_avg",
]

CATEGORICAL_FEATURES = [
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
]

DEMO_STUDENT_HASH = os.getenv(
    "BLEARN_DEMO_STUDENT_HASH",
    "79d86f4d0c556c37c879fb9ba278f9996d5f1f50468d8e26e13a19ba6b09c219",
)

DEMO_ITEM_SPECS = [
    (
        546803,
        [0.92, 0.12, 0.28],
        "Giới thiệu về Neural Networks (Học phần #546803)",
        "Video bài giảng",
        "Chương 1: Nền tảng Học máy",
        "Mở khóa",
        "35 phút",
    ),
    (
        546652,
        [0.84, 0.21, 0.34],
        "Tài liệu tóm tắt: Các thuật toán cốt lõi (Học phần #546652)",
        "PDF",
        "Chương 2: Thuật toán cốt lõi",
        "Mở khóa",
        "18 trang",
    ),
    (
        546732,
        [0.79, 0.27, 0.41],
        "Tối ưu hóa Mô hình Học máy Cơ bản (Học phần #546732)",
        "Tài liệu đọc",
        "Chương 3: Phân tích Dữ liệu Nâng cao",
        "Mở khóa",
        "28 phút",
    ),
]

# In-memory store for live features and BKT masteries of students
_student_live_features = {}  # {student_id_hash: {feature_name: value}}
_student_bkt_mastery = {}    # {student_id_hash: {chapter_id: p_L}}
lgbm_model = None

def get_student_features(student_hash: str) -> dict:
    # Try reading from shared cache first
    cached_feats = shared_cache.get("features", {}).get(student_hash)
    if cached_feats is not None:
        return cached_feats

    global _student_live_features
    if student_hash not in _student_live_features:
        # Khởi tạo mặc định
        features_dict = {col: 0.0 for col in GOLD_FEATURE_COLUMNS}
        for cat in CATEGORICAL_FEATURES:
            features_dict[cat] = "Unknown"
        features_dict["code_module"] = "AAA"
        features_dict["code_presentation"] = "2014J"
        
        try:
            # Lấy df_risk_features từ cache
            _, _, _, _, df_feats, _ = get_cached_data()
            if df_feats is not None and not df_feats.empty:
                student_rows = df_feats[df_feats['student_id_hash'] == student_hash]
                if not student_rows.empty:
                    row_dict = student_rows.iloc[0].to_dict()
                    for col in GOLD_FEATURE_COLUMNS:
                        if col in row_dict:
                            features_dict[col] = row_dict[col]
        except Exception as e:
            print(f"Lỗi nạp baseline features cho {student_hash}: {e}")
            
        _student_live_features[student_hash] = features_dict
        
    # Write back to shared cache
    all_features = shared_cache.get("features", {})
    all_features[student_hash] = _student_live_features[student_hash]
    shared_cache.set("features", all_features)
        
    return _student_live_features[student_hash]


def get_student_bkt_mastery(student_hash: str) -> dict:
    # Try reading from shared cache first
    cached_bkt = shared_cache.get("bkt", {}).get(student_hash)
    if cached_bkt is not None:
        return cached_bkt

    global _student_bkt_mastery
    if student_hash not in _student_bkt_mastery:
        # Khởi tạo mặc định
        _student_bkt_mastery[student_hash] = {
            "C1": 0.40,
            "C2": 0.40,
            "C3": 0.40,
            "C4": 0.40,
            "C5": 0.40,
            "C6": 0.40,
        }
        try:
            # Lấy df_bkt_mastery từ cache
            _, _, _, _, _, df_bkt = get_cached_data()
            if df_bkt is not None and not df_bkt.empty:
                student_rows = df_bkt[df_bkt['user_id'] == student_hash]
                for _, row in student_rows.iterrows():
                    skill = str(row['skill_name'])
                    for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]:
                        if ch in skill:
                            _student_bkt_mastery[student_hash][ch] = float(row['state_predictions'])
        except Exception as e:
            print(f"Lỗi nạp baseline BKT cho {student_hash}: {e}")
            
    # Write back to shared cache
    all_bkt = shared_cache.get("bkt", {})
    all_bkt[student_hash] = _student_bkt_mastery[student_hash]
    shared_cache.set("bkt", all_bkt)
            
    return _student_bkt_mastery[student_hash]

def get_student_risk(student_hash: str) -> float:
    cached_risk = shared_cache.get("risk", {}).get(student_hash)
    if cached_risk is not None:
        return float(cached_risk)
    
    global _student_risk_dict
    risk = _student_risk_dict.get(student_hash, 0.0)
    shifts = shared_cache.get("shifts", {})
    if student_hash in shifts:
        risk = max(0.0, min(1.0, risk - shifts[student_hash]))
    return float(risk)


def load_lgbm_model():
    """Tải và nạp mô hình LightGBM từ local cache hoặc Azure Storage."""
    global lgbm_model
    if lgbm_model is not None:
        return lgbm_model
        
    local_model_path = "/tmp/oulad_lgbm_pipeline.joblib"
    
    if not os.path.exists(local_model_path):
        try:
            if storage_key:
                container_client = ContainerClient(
                    account_url=f"https://{storage_account}.blob.core.windows.net",
                    container_name="gold",
                    credential=storage_key
                )
                for model_blob in ["models/oulad_lgbm_pipeline.joblib", "models/lightgbm_model.pkl"]:
                    try:
                        blob_client = container_client.get_blob_client(model_blob)
                        stream = io.BytesIO()
                        blob_client.download_blob().readinto(stream)
                        stream.seek(0)
                        lgbm_model = joblib.load(stream)
                        # Ghi cache file local
                        with open(local_model_path, "wb") as f:
                            f.write(stream.getvalue())
                        print(f"Loaded LGBM model from blob {model_blob}")
                        return lgbm_model
                    except Exception:
                        continue
            
            # Tải từ public URL của storage
            import urllib.request
            for url in [
                f"https://{storage_account}.blob.core.windows.net/gold/models/oulad_lgbm_pipeline.joblib",
                f"https://{storage_account}.blob.core.windows.net/gold/models/lightgbm_model.pkl"
            ]:
                try:
                    urllib.request.urlretrieve(url, local_model_path)
                    print(f"Downloaded LGBM model from public URL: {url}")
                    lgbm_model = joblib.load(local_model_path)
                    return lgbm_model
                except Exception:
                    continue
        except Exception as e:
            print(f"Lỗi tải LGBM model: {e}")
            
    if os.path.exists(local_model_path):
        try:
            lgbm_model = joblib.load(local_model_path)
            return lgbm_model
        except Exception as e:
            print(f"Lỗi load cached LGBM model: {e}")
            
    return None


def _build_offline_demo_frame(file_name: str) -> pd.DataFrame:
    """Sinh dữ liệu demo tối thiểu khi Serving artifacts chưa materialize được."""
    if file_name == "user_embeddings.parquet":
        return pd.DataFrame([
            {
                "student_id_hash": DEMO_STUDENT_HASH,
                "user_embedding": [0.88, 0.18, 0.31],
            },
            {
                "student_id_hash": "demo_peer_student_hash",
                "user_embedding": [0.25, 0.64, 0.55],
            },
        ])

    if file_name == "item_embeddings.parquet":
        return pd.DataFrame([
            {"id_site": item_id, "item_embedding": embedding}
            for item_id, embedding, *_ in DEMO_ITEM_SPECS
        ])

    if file_name == "risk_predictions.parquet":
        return pd.DataFrame([
            {
                "student_id_hash": DEMO_STUDENT_HASH,
                "dropout_probability": 0.18,
                "id_student": "demo-001",
                "highest_education": "Đại học",
            },
            {
                "student_id_hash": "demo_peer_student_hash",
                "dropout_probability": 0.63,
                "id_student": "demo-002",
                "highest_education": "Cao đẳng",
            },
        ])

    if file_name == "risk_features.parquet":
        base = {col: 0.0 for col in GOLD_FEATURE_COLUMNS}
        for cat in CATEGORICAL_FEATURES:
            base[cat] = "Unknown"
        base.update({
            "code_module": "AAA",
            "code_presentation": "2014J",
            "gender": "M",
            "region": "North",
            "highest_education": "Đại học",
            "imd_band": "50-60%",
            "age_band": "0-35",
            "disability": "N",
            "total_clicks": 182.0,
            "active_days": 14.0,
            "avg_daily_clicks": 13.0,
            "max_clicks_day": 31.0,
            "engagement_span": 21.0,
            "recent_weekly_rate": 9.0,
            "recency_days": 3.0,
            "engagement_momentum": 1.4,
            "avg_score": 78.0,
            "min_score": 62.0,
            "submission_count": 4.0,
            "late_submissions": 0.0,
            "weighted_avg": 78.0,
        })
        peer = base.copy()
        peer.update({
            "code_module": "BBB",
            "code_presentation": "2014B",
            "gender": "F",
            "region": "South",
            "highest_education": "Cao đẳng",
            "total_clicks": 74.0,
            "active_days": 6.0,
            "avg_daily_clicks": 12.0,
            "max_clicks_day": 18.0,
            "engagement_span": 10.0,
            "recent_weekly_rate": 5.0,
            "recency_days": 11.0,
            "engagement_momentum": -1.2,
            "avg_score": 54.0,
            "min_score": 42.0,
            "submission_count": 2.0,
            "late_submissions": 1.0,
            "weighted_avg": 54.0,
        })
        return pd.DataFrame([
            {"student_id_hash": DEMO_STUDENT_HASH, **base},
            {"student_id_hash": "demo_peer_student_hash", **peer},
        ])

    if file_name == "bkt_mastery.parquet":
        return pd.DataFrame([
            {"user_id": DEMO_STUDENT_HASH, "skill_name": "AAA_C1", "state_predictions": 0.84},
            {"user_id": DEMO_STUDENT_HASH, "skill_name": "AAA_C2", "state_predictions": 0.72},
            {"user_id": DEMO_STUDENT_HASH, "skill_name": "AAA_C3", "state_predictions": 0.88},
            {"user_id": DEMO_STUDENT_HASH, "skill_name": "AAA_C4", "state_predictions": 0.64},
            {"user_id": DEMO_STUDENT_HASH, "skill_name": "AAA_C5", "state_predictions": 0.76},
            {"user_id": DEMO_STUDENT_HASH, "skill_name": "AAA_C6", "state_predictions": 0.69},
        ])

    if file_name == "lms_simulator.parquet":
        rows = []
        for item_id, _, title, item_type, chapter, status, duration in DEMO_ITEM_SPECS:
            rows.append({
                "id_site": item_id,
                "title": title,
                "type": item_type,
                "chapter": chapter,
                "status": status,
                "duration": duration,
                "activity_title": title,
                "activity_name": title,
                "resource_name": title,
                "activity_type": item_type,
                "resource_type": item_type,
                "week_from": 1,
                "week_to": 2,
            })
        return pd.DataFrame(rows)

    raise FileNotFoundError(f"Không có fallback demo cho {file_name}")


def _parse_event_time(value) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        return value if value.tzinfo else value.replace(tzinfo=datetime.timezone.utc)
    if not value:
        return datetime.datetime.now(datetime.timezone.utc)
    try:
        parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


def _read_live_event_log() -> list[dict]:
    events = shared_cache.get("event_log", [])
    return events if isinstance(events, list) else []


def _append_live_event(record: dict) -> None:
    events = _read_live_event_log()
    events.append(record)
    shared_cache.set("event_log", events[-250:])


def _get_title_overrides() -> dict:
    overrides = shared_cache.get("title_overrides", {})
    return overrides if isinstance(overrides, dict) else {}


def _store_material_title_override(site_id: int | None, title: str, metadata: dict | None = None) -> None:
    if site_id is None:
        return
    cleaned_title = _coerce_text(title)
    if not cleaned_title:
        return

    overrides = _get_title_overrides()
    material_titles = overrides.get("material_titles", {})
    if not isinstance(material_titles, dict):
        material_titles = {}

    material_titles[str(site_id)] = {
        "title": cleaned_title,
        "type": _coerce_text((metadata or {}).get("material_type")),
        "chapter": _coerce_text((metadata or {}).get("material_chapter")),
        "duration": _coerce_text((metadata or {}).get("material_duration")),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    overrides["material_titles"] = material_titles
    shared_cache.set("title_overrides", overrides)


def _store_assignment_title_override(assignment_id: str, title: str, metadata: dict | None = None) -> None:
    cleaned_assignment_id = _coerce_text(assignment_id)
    cleaned_title = _coerce_text(title)
    if not cleaned_assignment_id or not cleaned_title:
        return

    overrides = _get_title_overrides()
    assignment_titles = overrides.get("assignment_titles", {})
    if not isinstance(assignment_titles, dict):
        assignment_titles = {}

    assignment_titles[cleaned_assignment_id] = {
        "title": cleaned_title,
        "chapter_id": _coerce_text((metadata or {}).get("chapter_id")),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    overrides["assignment_titles"] = assignment_titles
    shared_cache.set("title_overrides", overrides)


def _resolve_title_override(site_id: int | None = None, assignment_id: str | None = None) -> str:
    overrides = _get_title_overrides()
    if site_id is not None:
        material_titles = overrides.get("material_titles", {})
        if isinstance(material_titles, dict):
            entry = material_titles.get(str(site_id))
            if isinstance(entry, dict):
                title = _coerce_text(entry.get("title"))
                if title:
                    return title
            elif isinstance(entry, str):
                title = _coerce_text(entry)
                if title:
                    return title

    if assignment_id is not None:
        assignment_titles = overrides.get("assignment_titles", {})
        if isinstance(assignment_titles, dict):
            entry = assignment_titles.get(str(assignment_id))
            if isinstance(entry, dict):
                title = _coerce_text(entry.get("title"))
                if title:
                    return title
            elif isinstance(entry, str):
                title = _coerce_text(entry)
                if title:
                    return title

    return ""


def _count_student_events(student_hash: str, event_type: str | None = None) -> int:
    events = _read_live_event_log()
    count = 0
    for ev in events:
        if ev.get("student_id_hash") != student_hash:
            continue
        if event_type and ev.get("event_type") != event_type:
            continue
        count += 1
    return count


def _infer_chapter_id(assignment_id: str = "", explicit_chapter_id: str | None = None) -> str:
    """Resolve the real course chapter instead of relying only on reused OULAD ids."""
    normalized_chapter = str(explicit_chapter_id or "").strip().upper()
    if normalized_chapter in {f"C{idx}" for idx in range(1, 7)}:
        return normalized_chapter

    assignment_text = str(assignment_id or "").strip().lower()
    for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]:
        if ch.lower() in assignment_text:
            return ch

    oulad_default_map = {
        "546803": "C1",
        "546652": "C2",
        "546732": "C3",
    }
    return oulad_default_map.get(str(assignment_id).strip(), "C1")


def _build_competency_progress(student_hash: str) -> dict:
    progress = {
        ch: {
            "score": 0,
            "submissions": 0,
            "correct_count": 0,
            "question_count": 0,
            "updated_at": None,
        }
        for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]
    }

    cached_progress = shared_cache.get("assessment_progress", {}).get(student_hash, {})
    if isinstance(cached_progress, dict):
        for ch, item in cached_progress.items():
            if ch in progress and isinstance(item, dict):
                progress[ch].update(item)
                if int(progress[ch].get("submissions", 0) or 0) <= 0 and float(progress[ch].get("score", 0) or 0) > 0:
                    progress[ch]["submissions"] = 1

    for ev in _read_live_event_log():
        if ev.get("student_id_hash") != student_hash or ev.get("event_type") != "assessment_submission":
            continue
        ch = _infer_chapter_id(ev.get("assignment_id", ""), ev.get("chapter_id"))
        if ch not in progress:
            continue
        event_time = _parse_event_time(ev.get("event_time")).isoformat()
        score = int(round(float(ev.get("score", 0.0))))
        previous_submissions = int(progress[ch].get("submissions", 0) or 0)
        if progress[ch]["updated_at"] is None or event_time > str(progress[ch]["updated_at"]):
            progress[ch] = {
                "score": max(0, min(100, score)),
                "submissions": previous_submissions + 1,
                "correct_count": int(ev.get("correct_count") or 0),
                "question_count": int(ev.get("question_count") or 0),
                "updated_at": event_time,
            }

    return progress


def _build_activity_levels(student_hash: str, days: int = 26 * 7) -> list[int]:
    events = _read_live_event_log()
    if not events:
        return []
    today = datetime.datetime.now(datetime.timezone.utc).date()
    counts = [0 for _ in range(days)]

    for ev in events:
        if ev.get("student_id_hash") != student_hash:
            continue
        event_time = _parse_event_time(ev.get("event_time"))
        delta_days = (today - event_time.date()).days
        if 0 <= delta_days < days:
            counts[days - 1 - delta_days] += 1

    max_count = max(counts) if counts else 0
    if max_count <= 0:
        return []

    levels = []
    for count in counts:
        level = int(round((count / max_count) * 4)) + 1
        levels.append(max(1, min(5, level)))
    return levels


def _activity_label_for_event(event: dict, lms_lookup: dict[int, dict]) -> str:
    if event.get("event_type") == "assessment_submission":
        assignment_title = _coerce_text(event.get("assignment_title"))
        if assignment_title:
            return f"Nộp bài: {assignment_title}"
        override_title = _resolve_title_override(assignment_id=event.get("assignment_id"))
        if override_title:
            return f"Nộp bài: {override_title}"
        assignment_id = str(event.get("assignment_id", "")).strip()
        if assignment_id:
            return f"Nộp bài {assignment_id}"
        return "Nộp bài"

    material_title = _coerce_text(event.get("material_title"))
    if material_title:
        return f"Xem tài liệu: {material_title}"

    site_id_raw = event.get("id_site")
    try:
        site_id = int(site_id_raw)
    except Exception:
        site_id = None

    override_title = _resolve_title_override(site_id=site_id)
    if override_title:
        return f"Xem tài liệu: {override_title}"

    if site_id is not None and site_id in lms_lookup:
        record = lms_lookup[site_id]
        value = _best_record_text(
            record,
            ["title", "activity_title", "activity_name", "resource_name", "name", "display_name", "label", "summary", "description"],
        )
        if value:
            return value
    return f"Xem tài liệu #{site_id_raw}" if site_id_raw is not None else "Xem tài liệu"


def _build_recent_sessions(student_hash: str, lms_lookup: dict[int, dict], limit: int = 4) -> list[dict]:
    events = [
        ev for ev in _read_live_event_log()
        if ev.get("student_id_hash") == student_hash and ev.get("event_type") in {"material_view", "assessment_submission"}
    ]
    if not events:
        return []

    recent_events = sorted(events, key=lambda ev: _parse_event_time(ev.get("event_time")), reverse=True)
    result = []
    seen_labels = set()
    for ev in recent_events:
        label = _activity_label_for_event(ev, lms_lookup)
        label_key = f"{ev.get('event_type')}::{label}"
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)
        if ev.get("event_type") == "assessment_submission":
            duration_seconds = int(ev.get("duration_seconds") or 0)
            duration_minutes = max(1, int(np.ceil(duration_seconds / 60.0))) if duration_seconds > 0 else 15
            result.append({
                "title": label,
                "kind": "assessment",
                "score": int(round(float(ev.get("score", 0.0)))),
                "time": duration_minutes,
            })
            continue

        duration_seconds = int(ev.get("duration_seconds") or 0)
        if duration_seconds > 0:
            duration_minutes = max(1, int(np.ceil(duration_seconds / 60.0)))
        else:
            clicks = max(1, int(ev.get("sum_click", 1) or 1))
            duration_minutes = max(1, min(20, int(np.ceil(clicks * 3 / 1.0))))
        result.append({
            "title": label,
            "kind": "material",
            "score": None,
            "time": duration_minutes,
        })
        if len(result) >= limit:
            break
    return result


def _recent_learning_events(student_hash: str, limit: int = 20) -> list[dict]:
    events = [
        ev for ev in _read_live_event_log()
        if ev.get("student_id_hash") == student_hash and ev.get("event_type") in {"click", "material_view", "assessment_submission"}
    ]
    return sorted(events, key=lambda ev: _parse_event_time(ev.get("event_time")), reverse=True)[:limit]


lgbm_explainer = None

def get_shap_explanation(feats: dict) -> list:
    global lgbm_explainer
    model_pipeline = load_lgbm_model()
    if model_pipeline is None:
        return []
    
    try:
        preprocessor = model_pipeline.named_steps["preprocessor"]
        model = model_pipeline.named_steps["model"]
        
        if lgbm_explainer is None:
            import shap
            lgbm_explainer = shap.TreeExplainer(model)
            
        df_input = pd.DataFrame([feats])
        X_proc = preprocessor.transform(df_input)
        
        # Calculate SHAP values
        shap_vals = lgbm_explainer.shap_values(X_proc)
        
        # Identify feature impact on class 0 (Fail / dropout)
        if isinstance(shap_vals, list):
            fail_shap = shap_vals[0][0]
        elif isinstance(shap_vals, np.ndarray):
            if len(shap_vals.shape) == 3:
                fail_shap = shap_vals[0, :, 0]
            else:
                fail_shap = shap_vals[0]
        else:
            fail_shap = shap_vals[0]
            
        numeric_feats = [col for col in GOLD_FEATURE_COLUMNS if col not in CATEGORICAL_FEATURES]
        feature_names = numeric_feats + CATEGORICAL_FEATURES
        shap_dict = dict(zip(feature_names, fail_shap))
        
        # Sort by value descending (positive contribution to failure class)
        sorted_shap = sorted(shap_dict.items(), key=lambda x: x[1], reverse=True)
        
        feature_descriptions = {
            "total_clicks": "Tương tác học tập thấp (tổng số click chuột)",
            "active_days": "Số ngày tham gia học tập trực tuyến quá ít",
            "avg_daily_clicks": "Số lượt tương tác trung bình mỗi ngày thấp",
            "max_clicks_day": "Không có phiên học tập tương tác cao đột phá",
            "engagement_span": "Thời gian gắn bó/duy trì học tập ngắn",
            "recent_weekly_rate": "Tần suất học tập trong tuần gần đây giảm sút",
            "recency_days": "Đã lâu không truy cập hệ thống học tập",
            "engagement_momentum": "Động lực học tập/tương tác sụt giảm",
            "avg_score": "Điểm số trung bình các bài kiểm tra thấp",
            "min_score": "Điểm kiểm tra thấp nhất ở mức báo động",
            "submission_count": "Số lượng bài tập đã nộp chưa đạt yêu cầu",
            "late_submissions": "Tỉ lệ nộp bài muộn cao hoặc trễ hạn",
            "weighted_avg": "Điểm số trọng số học phần thấp",
            "num_of_prev_attempts": "Đã từng trượt hoặc học lại học phần này trước đó",
            "studied_credits": "Đang đăng ký học quá nhiều tín chỉ cùng lúc (gây quá tải)",
            "highest_education": "Trình độ học vấn đầu vào thấp",
            "imd_band": "Hoàn cảnh điều kiện kinh tế khó khăn",
            "age_band": "Độ tuổi học viên ảnh hưởng đến tiến độ học",
            "disability": "Học viên gặp hạn chế về mặt sức khỏe/khuyết tật",
            "region": "Vùng địa lý khó khăn tiếp cận hạ tầng học tập",
            "gender": "Các yếu tố nhân khẩu học giới tính ảnh hưởng",
            "code_module": "Mã học phần đặc thù có tỉ lệ trượt cao",
            "code_presentation": "Học kỳ học tập có độ khó cao"
        }
        
        top_3 = []
        for feat, val in sorted_shap:
            if len(top_3) >= 3:
                break
            desc = feature_descriptions.get(feat, f"Đặc trưng {feat}")
            top_3.append({
                "feature": feat,
                "impact": float(val),
                "description": desc
            })
            
        return top_3
    except Exception as e:
        print(f"Error calculating SHAP: {e}")
        return []


def _run_live_risk_inference(student_hash: str, feats: dict):
    global df_risk, _student_risk_dict
    model = load_lgbm_model()
    if model is not None:
        try:
            df_input = pd.DataFrame([feats])
            prob = model.predict_proba(df_input[GOLD_FEATURE_COLUMNS])[0]
            # Success index is 1
            dropout_prob = float(1.0 - prob[1])
            
            # Cập nhật trực tiếp vào cache df_risk
            user_emb_df, item_emb_df, risk_df, lms_meta_df, _, _ = get_cached_data()
            if risk_df is not None and not risk_df.empty:
                idx_list = risk_df[risk_df['student_id_hash'] == student_hash].index
                for idx in idx_list:
                    risk_df.loc[idx, 'dropout_probability'] = dropout_prob
            _student_risk_dict[student_hash] = dropout_prob
            
            # Update shared cache risk
            all_risk = shared_cache.get("risk", {})
            all_risk[student_hash] = dropout_prob
            shared_cache.set("risk", all_risk)
            
            print(f"[LightGBM Live Inference] Updated student {student_hash} dropout_prob={dropout_prob:.4f}")
            return dropout_prob
        except Exception as e:
            print(f"Lỗi Live Inference LightGBM: {e}")
    return None


class LoginRequest(BaseModel):
    username: str
    role: str = "student"


class ClickTrackRequest(BaseModel):
    student_id_hash: str
    id_site: int
    material_title: Optional[str] = None
    material_type: Optional[str] = None
    material_chapter: Optional[str] = None
    material_duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    code_module: str = ""
    code_presentation: str = ""
    sum_click: int = 1
    event_type: str = "click"
    page_path: str = ""
    source: str = "frontend-demo"
    event_time: Optional[str] = None


class AssessmentSubmitRequest(BaseModel):
    student_id_hash: str
    assignment_id: str
    score: float
    chapter_id: Optional[str] = None
    assignment_title: Optional[str] = None
    duration_seconds: Optional[int] = None
    question_count: Optional[int] = None
    correct_count: Optional[int] = None


def _fallback_click_log_path() -> str:
    return os.getenv("CLICK_FALLBACK_LOG_PATH", "/tmp/fallback_clicks.log")


def _build_click_event(payload: ClickTrackRequest, current_user: dict) -> dict:
    return {
        "student_id_hash": payload.student_id_hash,
        "id_site": int(payload.id_site),
        "material_title": payload.material_title,
        "material_type": payload.material_type,
        "material_chapter": payload.material_chapter,
        "material_duration": payload.material_duration,
        "duration_seconds": int(payload.duration_seconds or 0),
        "code_module": payload.code_module,
        "code_presentation": payload.code_presentation,
        "sum_click": int(payload.sum_click),
        "event_type": payload.event_type,
        "page_path": payload.page_path,
        "source": payload.source,
        "event_time": payload.event_time or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "client_role": current_user.get("role"),
        "client_user": current_user.get("username"),
    }


def _get_click_producer() -> KafkaProducer:
    global click_producer
    if click_producer is None:
        bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        click_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
            linger_ms=0,
            acks=1,
            retries=0,
            max_block_ms=1000,
        )
    return click_producer


def _append_click_fallback(record: dict) -> None:
    log_path = _fallback_click_log_path()
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _publish_click_event(record: dict) -> None:
    try:
        producer = _get_click_producer()
        topic = os.getenv("KAFKA_TOPIC", "learning-events")
        producer.send(topic, record)
    except Exception as exc:
        print(f"Cảnh báo: Kafka unavailable, lưu click fallback vào file ({exc})")
        try:
            _append_click_fallback(record)
        except Exception as fallback_exc:
            print(f"Lỗi ghi fallback click log: {fallback_exc}")


def _publish_click_event_wrapper(record: dict) -> None:
    # A simple wrapper helper that logs exceptions
    try:
        _publish_click_event(record)
    except Exception as exc:
        print(f"Background thread failed publishing click event: {exc}")


def load_parquet_file(file_name: str) -> pd.DataFrame:
    """Tải tệp Parquet từ Local Cache của Pod hoặc ADLS Gen2."""
    local_cache_path = f"/tmp/{file_name}"
    repo_candidates = [
        REPO_ROOT / file_name,
        REPO_ROOT / "data" / file_name,
        REPO_ROOT / "benchmarks" / file_name,
    ]

    for candidate in repo_candidates:
        if candidate.exists():
            try:
                return pd.read_parquet(candidate)
            except Exception as e:
                print(f"Local repo cache read failed for {candidate}: {e}")

    if os.path.exists(local_cache_path):
        try:
            return pd.read_parquet(local_cache_path)
        except Exception as e:
            print(f"Local tmp cache read failed for {local_cache_path}: {e}")

    url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data/{file_name}"

    try:
        if not storage_key:
            return pd.read_parquet(url)

        container_client = ContainerClient(
            account_url=f"https://{storage_account}.blob.core.windows.net",
            container_name="serving",
            credential=storage_key
        )
        prefix = f"ui_data/{file_name}/"
        blobs = container_client.list_blobs(name_starts_with=prefix)
        dfs = []

        for b in blobs:
            if b.name.endswith('.parquet') and b.size > 0:
                stream = io.BytesIO()
                container_client.get_blob_client(b.name).download_blob().readinto(stream)
                stream.seek(0)
                dfs.append(pd.read_parquet(stream))

        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df.to_parquet(local_cache_path)
        else:
            df = pd.read_parquet(url)
            df.to_parquet(local_cache_path)
    except Exception as exc:
        print(f"Cảnh báo: không tải được {file_name} từ Azure/cache ({exc}); dùng dữ liệu demo offline.")
        return _build_offline_demo_frame(file_name)

    if os.path.exists(local_cache_path):
        try:
            return pd.read_parquet(local_cache_path)
        except Exception as exc:
            print(f"Local cache read after refresh failed for {local_cache_path}: {exc}")

    return _build_offline_demo_frame(file_name)


def _coerce_text(value, fallback: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _best_record_text(record: dict, preferred_keys: list[str]) -> str:
    for key in preferred_keys:
        value = _coerce_text(record.get(key))
        if value and value.upper() not in {"AAA", "BBB", "CCC"}:
            return value

    for key, value in record.items():
        lowered = str(key).lower()
        if any(token in lowered for token in ["title", "name", "label", "summary", "description", "content", "resource", "activity"]):
            text = _coerce_text(value)
            if text and text.upper() not in {"AAA", "BBB", "CCC"}:
                return text

    return ""


def _normalize_content_type(raw_type: str, idx: int) -> str:
    lowered = raw_type.lower()
    if any(token in lowered for token in ["video", "lecture", "audio"]):
        return "Video bài giảng"
    if any(token in lowered for token in ["pdf", "file", "document", "reading", "book"]):
        return "PDF"
    return "Video bài giảng" if idx % 2 == 0 else "PDF"


def _format_duration(record: dict, idx: int) -> str:
    for field in ["duration", "estimated_time", "estimated_minutes", "minutes"]:
        value = record.get(field)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        try:
            minutes = int(float(value))
            if minutes > 0:
                return f"{minutes} phút"
        except (TypeError, ValueError):
            text = _coerce_text(value)
            if text:
                return text

    for field in ["pages", "page_count"]:
        value = record.get(field)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        try:
            pages = int(float(value))
            if pages > 0:
                return f"{pages} trang"
        except (TypeError, ValueError):
            text = _coerce_text(value)
            if text:
                return text

    return "25 phút" if idx % 2 == 0 else "12 trang"


def _format_chapter(record: dict) -> str:
    chapter = _coerce_text(record.get("chapter"))
    if chapter:
        return chapter

    week_from = record.get("week_from")
    week_to = record.get("week_to")
    if week_from is not None and week_to is not None and not pd.isna(week_from) and not pd.isna(week_to):
        try:
            return f"Tuần {int(float(week_from))} - {int(float(week_to))}"
        except (TypeError, ValueError):
            pass

    return "Chương 1: Phân tích hành vi & Gợi ý cá nhân hóa"


def _material_from_lookup(site_id: int, score: float, idx: int, lms_by_site: dict) -> dict:
    record = lms_by_site.get(site_id, {})
    raw_title = _resolve_title_override(site_id=site_id) or _best_record_text(
        record,
        ["title", "activity_title", "activity_name", "resource_name", "name", "display_name", "label", "summary", "description"],
    )
    raw_type = (
        _coerce_text(record.get("type"))
        or _coerce_text(record.get("activity_type"))
        or _coerce_text(record.get("resource_type"))
    )
    status = _coerce_text(record.get("status"), "Mở khóa")

    return {
        "id": f"m-{site_id}",
        "title": raw_title or f"Tài liệu tương tác chuyên sâu học phần #{site_id}",
        "type": _normalize_content_type(raw_type, idx),
        "duration": _format_duration(record, idx),
        "status": status,
        "chapter": _format_chapter(record),
        "id_site": site_id,
        "score": float(score),
    }


def _build_lms_lookup(df_meta: pd.DataFrame) -> dict:
    if df_meta is None or df_meta.empty or "id_site" not in df_meta.columns:
        return {}

    normalized = df_meta.copy()
    normalized["id_site"] = pd.to_numeric(normalized["id_site"], errors="coerce")
    normalized = normalized.dropna(subset=["id_site"]).drop_duplicates(subset=["id_site"], keep="first")

    records = normalized.to_dict(orient="records")
    return {int(row["id_site"]): row for row in records}


def get_cached_data():
    global df_user_emb, df_item_emb, df_risk, df_lms_meta, df_risk_features, df_bkt_mastery, last_loaded
    global _user_emb_dict, _item_emb_matrix, _item_ids_list, _student_risk_dict, _lms_by_site_cache, _student_bkt_mastery, _student_live_features
    now = datetime.datetime.now()
    # Cache hết hạn sau 5 phút
    if last_loaded is None or (now - last_loaded).total_seconds() > 300:
        try:
            df_user_emb = load_parquet_file("user_embeddings.parquet")
            df_item_emb = load_parquet_file("item_embeddings.parquet")
            df_risk = load_parquet_file("risk_predictions.parquet")
            
            try:
                df_risk_features = load_parquet_file("risk_features.parquet")
            except Exception as e_f:
                print(f"Cảnh báo: không tải được risk_features.parquet ({e_f})")
                df_risk_features = pd.DataFrame()
                
            try:
                df_bkt_mastery = load_parquet_file("bkt_mastery.parquet")
            except Exception as e_b:
                print(f"Cảnh báo: không tải được bkt_mastery.parquet ({e_b})")
                df_bkt_mastery = pd.DataFrame()
            
            try:
                df_lms_meta = load_parquet_file("lms_simulator.parquet")
            except Exception as lms_error:
                print(f"Cảnh báo: không tải được lms_simulator.parquet ({lms_error})")
                df_lms_meta = pd.DataFrame()

            # Pre-compute fast lookup structures
            if not df_user_emb.empty:
                _user_emb_dict = {
                    row["student_id_hash"]: np.array(row["user_embedding"])
                    for row in df_user_emb.to_dict(orient="records")
                }
            else:
                _user_emb_dict = {}
                
            if not df_item_emb.empty:
                _item_ids_list = df_item_emb["id_site"].tolist()
                _item_emb_matrix = np.stack(df_item_emb["item_embedding"].values)
            else:
                _item_ids_list = []
                _item_emb_matrix = None
                
            if not df_risk.empty:
                _student_risk_dict = {
                    row["student_id_hash"]: float(row["dropout_probability"])
                    for row in df_risk.to_dict(orient="records")
                }
            else:
                _student_risk_dict = {}
                
            _lms_by_site_cache = _build_lms_lookup(df_lms_meta)

            # Pre-populate BKT mastery cache
            _student_bkt_mastery = {}
            if not df_bkt_mastery.empty:
                for row in df_bkt_mastery.to_dict(orient="records"):
                    uid = row.get("user_id")
                    skill = str(row.get("skill_name", ""))
                    val = float(row.get("state_predictions", 0.40))
                    if uid:
                        if uid not in _student_bkt_mastery:
                            _student_bkt_mastery[uid] = {ch: 0.40 for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]}
                        for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]:
                            if ch in skill:
                                _student_bkt_mastery[uid][ch] = val

            # Pre-populate risk features cache
            _student_live_features = {}
            if not df_risk_features.empty:
                for row in df_risk_features.to_dict(orient="records"):
                    shash = row.get("student_id_hash")
                    if shash:
                        feats_dict = {col: row.get(col, 0.0) for col in GOLD_FEATURE_COLUMNS}
                        for cat in CATEGORICAL_FEATURES:
                            feats_dict[cat] = row.get(cat, "Unknown")
                        _student_live_features[shash] = feats_dict

            # Áp dụng các thay đổi từ submit-assessment đã lưu
            if df_risk is not None and not df_risk.empty:
                shifts = shared_cache.get("shifts", {})
                for shash, reduction in shifts.items():
                    idx_list = df_risk[df_risk['student_id_hash'] == shash].index
                    for idx in idx_list:
                        df_risk.loc[idx, 'dropout_probability'] = max(0.0, min(1.0, float(df_risk.loc[idx, 'dropout_probability']) - reduction))
                    if shash in _student_risk_dict:
                        _student_risk_dict[shash] = max(0.0, min(1.0, _student_risk_dict[shash] - reduction))

            last_loaded = now
            print(f"[{now.isoformat()}] Dữ liệu phục vụ đã được làm mới thành công.")
        except Exception as e:
            print(f"Lỗi tải dữ liệu: {e}")
            if df_user_emb is None:
                # Mock dự phòng
                df_user_emb = pd.DataFrame()
                df_item_emb = pd.DataFrame()
                df_risk = pd.DataFrame()
                df_lms_meta = pd.DataFrame()
                df_risk_features = pd.DataFrame()
                df_bkt_mastery = pd.DataFrame()
                _user_emb_dict = {}
                _item_emb_matrix = None
                _item_ids_list = []
                _student_risk_dict = {}
                _lms_by_site_cache = {}
    return df_user_emb, df_item_emb, df_risk, df_lms_meta, df_risk_features, df_bkt_mastery

# Bảo mật và JWT logic
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT Token không hợp lệ",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT Token đã hết hạn hoặc không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API Routes
@app.post("/login")
def login(payload: LoginRequest):
    """Tạo JWT access token. Demo chấp nhận mọi tài khoản hợp lệ."""
    access_token = create_access_token(
        data={"sub": payload.username, "role": payload.role},
        expires_delta=datetime.timedelta(hours=24)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/track-click")
def track_click(
    payload: ClickTrackRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
):
    """Nhận clickstream từ frontend và đẩy Kafka ở nền để tránh chặn UI."""
    record = _build_click_event(payload, current_user)
    _store_material_title_override(int(payload.id_site), payload.material_title or "", payload.model_dump())
    _append_live_event(record)
    background_tasks.add_task(_publish_click_event_wrapper, record)
    
    # Cập nhật Online Feature Extractor cho LightGBM Live Inference
    if payload.student_id_hash:
        try:
            feats = get_student_features(payload.student_id_hash)
            clicks = float(payload.sum_click)
            feats["total_clicks"] += clicks
            feats["active_days"] = max(1.0, feats["active_days"] + 0.1) # Tăng nhẹ active days
            feats["avg_daily_clicks"] = feats["total_clicks"] / feats["active_days"]
            feats["max_clicks_day"] = max(feats["max_clicks_day"], clicks)
            feats["engagement_span"] += 1.0
            feats["recent_weekly_rate"] = (feats["recent_weekly_rate"] * 6.0 + clicks) / 7.0
            feats["engagement_momentum"] = feats["recent_weekly_rate"] - feats["avg_daily_clicks"]
            
            # Khởi chạy Live Inference ngầm
            background_tasks.add_task(_run_live_risk_inference, payload.student_id_hash, feats)
        except Exception as e_click_feat:
            print(f"Lỗi cập nhật click features cho LGBM: {e_click_feat}")
            
    return {
        "accepted": True,
        "queued": True,
        "topic": os.getenv("KAFKA_TOPIC", "learning-events"),
        "event_time": record["event_time"],
    }

@app.get("/recommendations/{student_id_hash}")
def get_recommendations(student_id_hash: str, current_user: dict = Depends(verify_token)):
    """Tính toán RecSys realtime dựa trên vector nhúng LightGCN."""
    get_cached_data()
    
    global _user_emb_dict, _item_emb_matrix, _item_ids_list, _student_risk_dict, _lms_by_site_cache
    
    if not _user_emb_dict or _item_emb_matrix is None:
        raise HTTPException(status_code=503, detail="Dịch vụ lưu trữ dữ liệu Serving chưa sẵn sàng.")
        
    if student_id_hash not in _user_emb_dict:
        raise HTTPException(status_code=404, detail="Không tìm thấy vector nhúng của học viên.")
        
    u_emb = _user_emb_dict[student_id_hash]
    raw_scores = np.dot(_item_emb_matrix, u_emb)
    user_norm = float(np.linalg.norm(u_emb) or 1.0)
    item_norms = np.linalg.norm(_item_emb_matrix, axis=1)
    cosine_scores = raw_scores / (item_norms * user_norm + 1e-9)
    base_match_percent = np.clip((cosine_scores + 1.0) * 50.0, 0.0, 100.0)

    lms_by_site = _lms_by_site_cache
    ranked_recs = []
    for item_index, item_id in enumerate(_item_ids_list):
        sid = int(item_id)
        base_percent = float(base_match_percent[item_index])
        candidate = _material_from_lookup(sid, base_percent / 100.0, item_index, lms_by_site)
        candidate["score"] = float(base_percent / 100.0)
        candidate["rank_score"] = float(base_percent / 100.0)
        candidate["match_percent"] = int(round(base_percent))
        ranked_recs.append(candidate)

    ranked_recs.sort(key=lambda item: item.get("rank_score", item.get("score", 0.0)), reverse=True)
    recs = ranked_recs[:5]
    
    dropout_prob = get_student_risk(student_id_hash)
    
    # Live BKT mastery lookup
    bkt_mastery = get_student_bkt_mastery(student_id_hash)
    if not bkt_mastery:
        bkt_mastery = {
            "C1": 0.86,
            "C2": 0.72,
            "C3": 0.91,
            "C4": 0.64,
            "C5": 0.78,
            "C6": 0.69
        }
    
    feats = get_student_features(student_id_hash)
    shap_explanation = get_shap_explanation(feats)
    recent_sessions = _build_recent_sessions(student_id_hash, lms_by_site)
    activity_levels = _build_activity_levels(student_id_hash)
    competency_progress = _build_competency_progress(student_id_hash)
    click_count = _count_student_events(student_id_hash, "click")
    submission_count = _count_student_events(student_id_hash, "assessment_submission")
    live_event_count = len(_read_live_event_log())
    weekly_minutes = int(round(click_count * 2.5 + submission_count * 12.0)) if live_event_count > 0 else 0
    
    return {
        "student_id_hash": student_id_hash,
        "dropout_probability": dropout_prob,
        "recommendations": recs,
        "bkt_mastery": bkt_mastery,
        "competency_progress": competency_progress,
        "shap_explanation": shap_explanation,
        "activity_levels": activity_levels,
        "recent_sessions": recent_sessions,
        "activity_summary": {
            "weekly_minutes": weekly_minutes,
            "click_count": click_count,
            "submission_count": submission_count,
        },
        "data_source": {
            "mode": "live_event_log" if live_event_count > 0 else "seeded_cache",
            "event_log_count": live_event_count,
            "features_cached": bool(shared_cache.get("features", {}).get(student_id_hash)),
            "bkt_cached": bool(shared_cache.get("bkt", {}).get(student_id_hash)),
            "risk_cached": bool(shared_cache.get("risk", {}).get(student_id_hash)),
        },
        "served_by": "FastAPI Gateway",
        "client_role": current_user.get("role"),
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/submit-assessment")
def submit_assessment(
    payload: AssessmentSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
):
    """
    Nhận kết quả bài tập của học viên, chạy công thức Bayesian BKT cập nhật
    trạng thái thấu hiểu kiến thức, chạy Online Feature Extractor + LightGBM Live Inference
    để tính xác suất rủi ro bỏ học, đồng thời gửi thông điệp thô vào Kafka.
    """
    global df_risk
    
    score_rate = float(payload.score)
    submit_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # 1. 🧠 PHASE 1: CẬP NHẬT TRẠNG THÁI KIẾN THỨC BKT QUA CÔNG THỨC BAYES
    chapter_id = _infer_chapter_id(payload.assignment_id, payload.chapter_id)
    _store_assignment_title_override(payload.assignment_id, payload.assignment_title or "", payload.model_dump())
            
    # BKT coefficients
    P_L0 = 0.40
    P_T = 0.15
    P_G = 0.20
    P_S = 0.10
    
    masteries = get_student_bkt_mastery(payload.student_id_hash)
    p_L = masteries.get(chapter_id, P_L0)
    
    # Giả lập 20 câu hỏi tương ứng với điểm số
    correct_count = int(round(20 * (score_rate / 100.0)))
    incorrect_count = 20 - correct_count
    
    for _ in range(correct_count):
        p_L_cond = (p_L * (1.0 - P_S)) / ((p_L * (1.0 - P_S)) + ((1.0 - p_L) * P_G))
        p_L = p_L_cond + (1.0 - p_L_cond) * P_T
        
    for _ in range(incorrect_count):
        p_L_cond = (p_L * P_S) / ((p_L * P_S) + ((1.0 - p_L) * (1.0 - P_G)))
        p_L = p_L_cond + (1.0 - p_L_cond) * P_T
        
    masteries[chapter_id] = float(p_L)
    _student_bkt_mastery[payload.student_id_hash] = masteries
    
    # Write BKT to shared cache
    all_bkt = shared_cache.get("bkt", {})
    all_bkt[payload.student_id_hash] = masteries
    shared_cache.set("bkt", all_bkt)

    question_count = int(payload.question_count or 20)
    submitted_correct_count = int(
        payload.correct_count
        if payload.correct_count is not None
        else round(question_count * (score_rate / 100.0))
    )
    progress_item = {
        "score": int(round(max(0.0, min(100.0, score_rate)))),
        "submissions": 1,
        "correct_count": max(0, min(question_count, submitted_correct_count)),
        "question_count": question_count,
        "updated_at": submit_time,
    }
    all_progress = shared_cache.get("assessment_progress", {})
    student_progress = all_progress.get(payload.student_id_hash, {})
    if chapter_id in student_progress:
        progress_item["submissions"] = int(student_progress[chapter_id].get("submissions", 0) or 0) + 1
    student_progress[chapter_id] = progress_item
    all_progress[payload.student_id_hash] = student_progress
    shared_cache.set("assessment_progress", all_progress)
    
    print(f"[BKT Bayes Update] Student {payload.student_id_hash} skill {chapter_id} mastery updated to {p_L:.4f}")
    
    # 2. 📉 PHASE 2: CẬP NHẬT DỰ BÁO RỦI RO LIVE INFERENCE LIGHTGBM
    feats = get_student_features(payload.student_id_hash)
    feats["submission_count"] += 1.0
    total_prev_score = feats["avg_score"] * (feats["submission_count"] - 1.0)
    feats["avg_score"] = (total_prev_score + score_rate) / feats["submission_count"]
    feats["min_score"] = min(feats["min_score"] if feats["submission_count"] > 1.0 else 100.0, score_rate)
    feats["weighted_avg"] = feats["avg_score"]
    
    # Write features to shared cache
    all_features = shared_cache.get("features", {})
    all_features[payload.student_id_hash] = feats
    shared_cache.set("features", all_features)
    
    # Thực hiện Live Inference
    live_dropout_prob = _run_live_risk_inference(payload.student_id_hash, feats)
    
    # Fallback nếu mô hình LGBM chưa được nạp
    if live_dropout_prob is None:
        reduction = 0.05 if score_rate >= 50.0 else -0.10
        
        # Write shift to shared cache
        all_shifts = shared_cache.get("shifts", {})
        all_shifts[payload.student_id_hash] = all_shifts.get(payload.student_id_hash, 0.0) + reduction
        shared_cache.set("shifts", all_shifts)
        
        # Calculate new risk
        baseline_risk = _student_risk_dict.get(payload.student_id_hash, 0.0)
        new_risk = max(0.0, min(1.0, baseline_risk - all_shifts[payload.student_id_hash]))
        
        # Write new risk to shared cache
        all_risk = shared_cache.get("risk", {})
        all_risk[payload.student_id_hash] = new_risk
        shared_cache.set("risk", all_risk)
        
        user_emb_df, item_emb_df, risk_df, lms_meta_df, _, _ = get_cached_data()
        if risk_df is not None and not risk_df.empty:
            idx_list = risk_df[risk_df['student_id_hash'] == payload.student_id_hash].index
            for idx in idx_list:
                risk_df.loc[idx, 'dropout_probability'] = new_risk
        if payload.student_id_hash in _student_risk_dict:
            _student_risk_dict[payload.student_id_hash] = new_risk
        message_alert = f"Nộp bài thành công! Điểm của bạn: {score_rate}%. (Fallback Risk Shift áp dụng)"
    else:
        message_alert = f"Nộp bài thành công! Điểm của bạn: {score_rate}%. Live Inference tính toán nguy cơ bỏ học là {(live_dropout_prob * 100):.1f}%."

    # 3. 🗄️ Bắn bản tin thô vào Kafka để Spark Structured Streaming lưu vết Silver Layer
    record = {
        "student_id_hash": payload.student_id_hash,
        "assignment_id": payload.assignment_id,
        "chapter_id": chapter_id,
        "assignment_title": payload.assignment_title,
        "duration_seconds": int(payload.duration_seconds or 0),
        "score": score_rate,
        "question_count": question_count,
        "correct_count": progress_item["correct_count"],
        "event_type": "assessment_submission",
        "event_time": submit_time,
        "code_module": "AAA",
        "code_presentation": "2014J",
        "client_user": current_user.get("username"),
        "client_role": current_user.get("role"),
    }
    _append_live_event(record)
    background_tasks.add_task(_publish_click_event_wrapper, record)
    
    # Lấy dropout prob hiện tại của student để trả về
    new_prob = get_student_risk(payload.student_id_hash)

    return {
        "status": "success",
        "message": message_alert,
        "student_id_hash": payload.student_id_hash,
        "chapter_id": chapter_id,
        "score": progress_item["score"],
        "correct_count": progress_item["correct_count"],
        "question_count": progress_item["question_count"],
        "new_dropout_probability": new_prob
    }


@app.post("/reset-assessment-shifts")
def reset_assessment_shifts(current_user: dict = Depends(verify_token)):
    """Reset các thay đổi rủi ro bỏ học (phục vụ việc chạy lại demo)."""
    global df_risk, _student_risk_dict
    shared_cache.clear()
    try:
        df_risk = load_parquet_file("risk_predictions.parquet")
        _student_risk_dict = {
            row["student_id_hash"]: float(row["dropout_probability"])
            for row in df_risk.to_dict(orient="records")
        }
        print("[Closed-Loop Reset] In-memory dropout shifts cleared and predictions reloaded.")
        return {"status": "success", "message": "Trạng thái demo đã được reset thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể reload dữ liệu dự báo rủi ro: {str(e)}")

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

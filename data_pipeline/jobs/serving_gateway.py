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

# Thêm root data_pipeline vào sys.path để giải quyết import module
PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

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

# Lưu vết các thay đổi độ thành thục/dropout rate để áp dụng lại nếu cache bị refresh
_assessment_shifts = {}  # {student_id_hash: dropout_probability_reduction}

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

# In-memory store for live features and BKT masteries of students
_student_live_features = {}  # {student_id_hash: {feature_name: value}}
_student_bkt_mastery = {}    # {student_id_hash: {chapter_id: p_L}}
lgbm_model = None

def get_student_features(student_hash: str) -> dict:
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
        
    return _student_live_features[student_hash]


def get_student_bkt_mastery(student_hash: str) -> dict:
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
            
    return _student_bkt_mastery[student_hash]


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


def _fallback_click_log_path() -> str:
    return os.getenv("CLICK_FALLBACK_LOG_PATH", "/tmp/fallback_clicks.log")


def _build_click_event(payload: ClickTrackRequest, current_user: dict) -> dict:
    return {
        "student_id_hash": payload.student_id_hash,
        "id_site": int(payload.id_site),
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
            "KAFKA_BOOTSTRAP_SERVERS", "kafka-service.blearn-medallion.svc.cluster.local:9092"
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

def load_parquet_file(file_name: str) -> pd.DataFrame:
    """Tải tệp Parquet từ Local Cache của Pod hoặc ADLS Gen2."""
    local_cache_path = f"/tmp/{file_name}"
    
    # Local mock nếu chạy offline
    if not storage_key:
        url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data/{file_name}"
        return pd.read_parquet(url)
        
    if not os.path.exists(local_cache_path):
        try:
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
                url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data"
                df = pd.read_parquet(f"{url}/{file_name}")
                df.to_parquet(local_cache_path)
        except Exception:
            url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data"
            df = pd.read_parquet(f"{url}/{file_name}")
            df.to_parquet(local_cache_path)
            
    if os.path.exists(local_cache_path):
        return pd.read_parquet(local_cache_path)
    raise FileNotFoundError(f"Không thể tìm thấy tệp dữ liệu {file_name}")

def _coerce_text(value, fallback: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    text = str(value).strip()
    return text if text else fallback


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
    raw_title = (
        _coerce_text(record.get("title"))
        or _coerce_text(record.get("activity_title"))
        or _coerce_text(record.get("activity_name"))
        or _coerce_text(record.get("resource_name"))
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
            _user_emb_dict = {
                row["student_id_hash"]: np.array(row["user_embedding"])
                for row in df_user_emb.to_dict(orient="records")
            }
            _item_ids_list = df_item_emb["id_site"].tolist()
            _item_emb_matrix = np.stack(df_item_emb["item_embedding"].values)
            _student_risk_dict = {
                row["student_id_hash"]: float(row["dropout_probability"])
                for row in df_risk.to_dict(orient="records")
            }
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
                for shash, reduction in _assessment_shifts.items():
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
    background_tasks.add_task(_publish_click_event, record)
    
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
    scores = np.dot(_item_emb_matrix, u_emb)
    
    top_k = 5
    if len(scores) <= top_k:
        top_indices = np.argsort(scores)[::-1]
    else:
        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        
    lms_by_site = _lms_by_site_cache
    recs = []
    for idx, index_val in enumerate(top_indices):
        sid = int(_item_ids_list[index_val])
        score_val = float(scores[index_val])
        recs.append(_material_from_lookup(sid, score_val, idx, lms_by_site))
        
    dropout_prob = _student_risk_dict.get(student_id_hash, 0.0)
    
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
    
    return {
        "student_id_hash": student_id_hash,
        "dropout_probability": dropout_prob,
        "recommendations": recs,
        "bkt_mastery": bkt_mastery,
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
    global df_risk, _assessment_shifts
    
    score_rate = float(payload.score)
    
    # 1. 🧠 PHASE 1: CẬP NHẬT TRẠNG THÁI KIẾN THỨC BKT QUA CÔNG THỨC BAYES
    chapter_id = "C1"
    for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]:
        if ch.lower() in payload.assignment_id.lower() or payload.assignment_id in ["546803", "546652", "546732"]:
            if payload.assignment_id == "546803":
                chapter_id = "C1"
            elif payload.assignment_id == "546652":
                chapter_id = "C2"
            elif payload.assignment_id == "546732":
                chapter_id = "C3"
            else:
                chapter_id = ch
            break
            
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
    print(f"[BKT Bayes Update] Student {payload.student_id_hash} skill {chapter_id} mastery updated to {p_L:.4f}")
    
    # 2. 📉 PHASE 2: CẬP NHẬT DỰ BÁO RỦI RO LIVE INFERENCE LIGHTGBM
    feats = get_student_features(payload.student_id_hash)
    feats["submission_count"] += 1.0
    total_prev_score = feats["avg_score"] * (feats["submission_count"] - 1.0)
    feats["avg_score"] = (total_prev_score + score_rate) / feats["submission_count"]
    feats["min_score"] = min(feats["min_score"] if feats["submission_count"] > 1.0 else 100.0, score_rate)
    feats["weighted_avg"] = feats["avg_score"]
    
    # Thực hiện Live Inference
    live_dropout_prob = _run_live_risk_inference(payload.student_id_hash, feats)
    
    # Fallback nếu mô hình LGBM chưa được nạp
    if live_dropout_prob is None:
        reduction = 0.05 if score_rate >= 50.0 else -0.10
        _assessment_shifts[payload.student_id_hash] = _assessment_shifts.get(payload.student_id_hash, 0.0) + reduction
        user_emb_df, item_emb_df, risk_df, lms_meta_df, _, _ = get_cached_data()
        if risk_df is not None and not risk_df.empty:
            idx_list = risk_df[risk_df['student_id_hash'] == payload.student_id_hash].index
            for idx in idx_list:
                risk_df.loc[idx, 'dropout_probability'] = max(0.0, min(1.0, float(risk_df.loc[idx, 'dropout_probability']) - reduction))
        global _student_risk_dict
        if payload.student_id_hash in _student_risk_dict:
            _student_risk_dict[payload.student_id_hash] = max(0.0, min(1.0, _student_risk_dict[payload.student_id_hash] - reduction))
        message_alert = f"Nộp bài thành công! Điểm của bạn: {score_rate}%. (Fallback Risk Shift áp dụng)"
    else:
        message_alert = f"Nộp bài thành công! Điểm của bạn: {score_rate}%. Live Inference tính toán nguy cơ bỏ học là {(live_dropout_prob * 100):.1f}%."

    # 3. 🗄️ Bắn bản tin thô vào Kafka để Spark Structured Streaming lưu vết Silver Layer
    record = {
        "student_id_hash": payload.student_id_hash,
        "assignment_id": payload.assignment_id,
        "score": score_rate,
        "event_type": "assessment_submission",
        "event_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "code_module": "AAA",
        "code_presentation": "2014J",
        "client_user": current_user.get("username"),
        "client_role": current_user.get("role"),
    }
    background_tasks.add_task(_publish_click_event, record)
    
    # Lấy dropout prob hiện tại của student để trả về
    new_prob = _student_risk_dict.get(payload.student_id_hash, 0.0)

    return {
        "status": "success",
        "message": message_alert,
        "student_id_hash": payload.student_id_hash,
        "new_dropout_probability": new_prob
    }


@app.post("/reset-assessment-shifts")
def reset_assessment_shifts(current_user: dict = Depends(verify_token)):
    """Reset các thay đổi rủi ro bỏ học (phục vụ việc chạy lại demo)."""
    global _assessment_shifts, df_risk, _student_risk_dict
    _assessment_shifts.clear()
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

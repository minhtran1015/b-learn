import os
import sys
import json
import jwt
import datetime
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

storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

# Cache dữ liệu trong bộ nhớ để tránh I/O mạng liên tục
df_user_emb = None
df_item_emb = None
df_risk = None
df_lms_meta = None
last_loaded = None
click_producer = None


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

    lookup = {}
    for _, row in normalized.iterrows():
        site_id = int(row["id_site"])
        lookup[site_id] = row.to_dict()
    return lookup


def get_cached_data():
    global df_user_emb, df_item_emb, df_risk, df_lms_meta, last_loaded
    now = datetime.datetime.now()
    # Cache hết hạn sau 5 phút
    if last_loaded is None or (now - last_loaded).total_seconds() > 300:
        try:
            df_user_emb = load_parquet_file("user_embeddings.parquet")
            df_item_emb = load_parquet_file("item_embeddings.parquet")
            df_risk = load_parquet_file("risk_predictions.parquet")
            try:
                df_lms_meta = load_parquet_file("lms_simulator.parquet")
            except Exception as lms_error:
                print(f"Cảnh báo: không tải được lms_simulator.parquet ({lms_error})")
                df_lms_meta = pd.DataFrame()
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
    return df_user_emb, df_item_emb, df_risk, df_lms_meta

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
    return {
        "accepted": True,
        "queued": True,
        "topic": os.getenv("KAFKA_TOPIC", "learning-events"),
        "event_time": record["event_time"],
    }

@app.get("/recommendations/{student_id_hash}")
def get_recommendations(student_id_hash: str, current_user: dict = Depends(verify_token)):
    """Tính toán RecSys realtime dựa trên vector nhúng LightGCN."""
    u_emb_df, i_emb_df, risk_df, lms_meta_df = get_cached_data()
    
    if u_emb_df.empty or i_emb_df.empty:
        raise HTTPException(status_code=503, detail="Dịch vụ lưu trữ dữ liệu Serving chưa sẵn sàng.")
        
    user_row = u_emb_df[u_emb_df['student_id_hash'] == student_id_hash]
    if user_row.empty:
        raise HTTPException(status_code=404, detail="Không tìm thấy vector nhúng của học viên.")
        
    u_emb = np.array(user_row.iloc[0]['user_embedding'])
    i_embs = np.stack(i_emb_df['item_embedding'].values)
    
    scores = np.dot(i_embs, u_emb)
    
    df_scored = i_emb_df.copy()
    df_scored['score'] = scores
    
    top_5 = df_scored.sort_values(by='score', ascending=False).head(5)

    lms_by_site = _build_lms_lookup(lms_meta_df)
    recs = []
    for idx, (_, row) in enumerate(top_5.iterrows()):
        sid = int(row['id_site'])
        recs.append(_material_from_lookup(sid, row['score'], idx, lms_by_site))
        
    student_risk_row = risk_df[risk_df['student_id_hash'] == student_id_hash]
    dropout_prob = float(student_risk_row.iloc[0]['dropout_probability']) if not student_risk_row.empty else 0.0
    
    return {
        "student_id_hash": student_id_hash,
        "dropout_probability": dropout_prob,
        "recommendations": recs,
        "served_by": "FastAPI Gateway",
        "client_role": current_user.get("role"),
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

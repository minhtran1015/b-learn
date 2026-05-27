import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── MODULE-LEVEL IN-MEMORY CACHE ───────────────────────────────────────────
# All Parquet files are loaded ONCE at startup into process RAM.
# Subsequent requests are served entirely from memory — zero network I/O per request.
_DATA_CACHE: dict[str, pd.DataFrame] = {}

STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")

def _fetch_parquet(file_name: str) -> pd.DataFrame:
    """Low-level fetch from Azure or HTTP fallback. Called only at startup."""
    try:
        if STORAGE_KEY:
            storage_options = {
                "account_name": STORAGE_ACCOUNT,
                "account_key": STORAGE_KEY
            }
            path = f"abfss://serving@{STORAGE_ACCOUNT}.dfs.core.windows.net/ui_data/{file_name}"
            logger.info(f"[CACHE] Fetching from ADLS: {path}")
            return pd.read_parquet(path, storage_options=storage_options)
        else:
            url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/serving/ui_data/{file_name}"
            logger.info(f"[CACHE] Fetching from HTTP: {url}")
            return pd.read_parquet(url)
    except Exception as e:
        logger.warning(f"[CACHE] Could not load {file_name}: {e}")
        raise

def get_cached(file_name: str) -> pd.DataFrame:
    """Return DataFrame from in-memory cache. Raises HTTPException if not loaded."""
    if file_name not in _DATA_CACHE:
        raise HTTPException(
            status_code=503,
            detail=f"Dữ liệu '{file_name}' chưa được nạp vào bộ nhớ. Vui lòng thử lại sau."
        )
    return _DATA_CACHE[file_name]

# ─── STARTUP: LOAD ALL DATA INTO RAM ────────────────────────────────────────
REQUIRED_FILES = [
    "risk_predictions.parquet",
    "bkt_mastery.parquet",
    "user_embeddings.parquet",
    "item_embeddings.parquet",
]
OPTIONAL_FILES = [
    "cohort_stats.parquet",
    "lms_simulator.parquet",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all serving Parquet files into RAM once at pod startup."""
    logger.info("=" * 60)
    logger.info("[STARTUP] Pre-loading all serving data into memory cache...")
    start = datetime.utcnow()

    for fname in REQUIRED_FILES:
        try:
            _DATA_CACHE[fname] = _fetch_parquet(fname)
            logger.info(f"[STARTUP] ✅ {fname} — {len(_DATA_CACHE[fname])} rows loaded")
        except Exception as e:
            logger.error(f"[STARTUP] ❌ REQUIRED file {fname} failed to load: {e}")

    for fname in OPTIONAL_FILES:
        try:
            _DATA_CACHE[fname] = _fetch_parquet(fname)
            logger.info(f"[STARTUP] ✅ {fname} (optional) — {len(_DATA_CACHE[fname])} rows loaded")
        except Exception as e:
            logger.warning(f"[STARTUP] ⚠️  Optional file {fname} skipped: {e}")

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(f"[STARTUP] Cache warm-up completed in {elapsed:.2f}s — {len(_DATA_CACHE)} files in memory")
    logger.info("=" * 60)
    yield
    # Shutdown: nothing to clean up
    _DATA_CACHE.clear()
    logger.info("[SHUTDOWN] Memory cache cleared.")

# ─── APP DEFINITION ──────────────────────────────────────────────────────────
app = FastAPI(
    title="B-LEARN Big Data Serving API",
    description="REST API phục vụ dữ liệu Gold Layer (OULAD) cho ứng dụng React Web frontend. Tất cả dữ liệu được nạp vào RAM khi khởi động để giảm độ trễ mạng.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

# API 1: Thống kê tổng quan toàn trường
@app.get("/api/v1/cohort/stats", summary="Lấy thống kê tổng quan toàn trường (Demographics & Clicks)")
def get_cohort_stats():
    df = get_cached("cohort_stats.parquet")
    df = df.replace({np.nan: None})
    return df.to_dict(orient="records")


# API 2: Thông tin rủi ro & độ thành thục của 1 sinh viên
@app.get("/api/v1/student/{student_id}", summary="Lấy thông tin rủi ro & độ thành thục của học viên")
def get_student_profile(student_id: str):
    df_risk = get_cached("risk_predictions.parquet")
    df_bkt = get_cached("bkt_mastery.parquet")

    student_risk = df_risk[df_risk['student_id_hash'] == student_id]
    if student_risk.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy thông tin rủi ro cho học viên {student_id}")

    student_bkt = df_bkt[df_bkt['user_id'] == student_id]

    risk_dict = student_risk.replace({np.nan: None}).to_dict(orient="records")[0]
    if "id_student" not in risk_dict:
        import hashlib
        val = int(hashlib.md5(student_id.encode('utf-8')).hexdigest()[:6], 16) % 900000 + 100000
        risk_dict["id_student"] = str(val)

    bkt_dict = student_bkt.replace({np.nan: None}).to_dict(orient="records")

    return {
        "student_id": student_id,
        "risk": risk_dict,
        "bkt_mastery": bkt_dict
    }


# API 3: Top 5 gợi ý tài liệu học tập cá nhân hóa
@app.get("/api/v1/student/{student_id}/recommendations", summary="Lấy top 5 gợi ý tài liệu học tập")
def get_student_recommendations(student_id: str):
    df_user_emb = get_cached("user_embeddings.parquet")
    df_item_emb = get_cached("item_embeddings.parquet")

    user_row = df_user_emb[df_user_emb['student_id_hash'] == student_id]
    if user_row.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ma trận nhúng của học viên {student_id}")

    u_emb = np.array(user_row.iloc[0]['user_embedding'])
    i_embs = np.stack(df_item_emb['item_embedding'].values)
    scores = np.dot(i_embs, u_emb)

    df_scored = df_item_emb.copy()
    df_scored['recommendation_score'] = scores
    top_5 = df_scored.sort_values(by='recommendation_score', ascending=False).head(5)

    if "lms_simulator.parquet" in _DATA_CACHE:
        df_lms = _DATA_CACHE["lms_simulator.parquet"]
        top_5 = top_5.merge(df_lms, on="id_site", how="left")
    else:
        top_5["activity_type"] = "resource"

    top_5["activity_type"] = top_5["activity_type"].fillna("resource")
    top_5 = top_5.replace({np.nan: None})

    results = []
    for _, row in top_5.iterrows():
        results.append({
            "id_site": str(row["id_site"]),
            "activity_type": str(row["activity_type"]),
            "recommendation_score": float(row["recommendation_score"])
        })

    return {
        "student_id": student_id,
        "recommendations": results
    }


# API 4: Danh sách học viên
@app.get("/api/v1/students", summary="Lấy danh sách các định danh học viên")
def get_student_list():
    df_risk = get_cached("risk_predictions.parquet")
    students = df_risk['student_id_hash'].unique().tolist()
    return {"students": students}


# API 5: Gửi sự kiện tương tác & nhận gợi ý cập nhật
class StudentInteraction(BaseModel):
    id_site: str
    activity_type: str

@app.post("/api/v1/student/{student_id}/interaction", summary="[POST] Gửi tương tác học viên & cập nhật gợi ý thời gian thực")
def record_interaction_and_recommend(student_id: str, interaction: StudentInteraction):
    """
    Nhận sự kiện tương tác (click tài liệu) từ React, giả lập dịch chuyển
    vector đặc trưng của học sinh và phản hồi danh sách gợi ý mới ngay lập tức.
    Tất cả tính toán thực hiện trên dữ liệu đã có sẵn trong RAM.
    """
    df_user_emb = get_cached("user_embeddings.parquet")
    df_item_emb = get_cached("item_embeddings.parquet")

    user_row = df_user_emb[df_user_emb['student_id_hash'] == student_id]
    if user_row.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ma trận nhúng của học viên {student_id}")

    u_emb = np.array(user_row.iloc[0]['user_embedding'])

    item_id_numeric = int(interaction.id_site) if interaction.id_site.isdigit() else None
    if item_id_numeric is not None:
        item_row = df_item_emb[df_item_emb['id_site'] == item_id_numeric]
    else:
        item_row = df_item_emb[df_item_emb['id_site'] == interaction.id_site]

    if not item_row.empty:
        i_emb = np.array(item_row.iloc[0]['item_embedding'])
        u_emb = u_emb + 0.3 * i_emb

    i_embs = np.stack(df_item_emb['item_embedding'].values)
    scores = np.dot(i_embs, u_emb)

    df_scored = df_item_emb.copy()
    df_scored['recommendation_score'] = scores
    top_5 = df_scored.sort_values(by='recommendation_score', ascending=False).head(5)

    if "lms_simulator.parquet" in _DATA_CACHE:
        df_lms = _DATA_CACHE["lms_simulator.parquet"]
        top_5 = top_5.merge(df_lms, on="id_site", how="left")
    else:
        top_5["activity_type"] = "resource"

    top_5["activity_type"] = top_5["activity_type"].fillna("resource")
    top_5 = top_5.replace({np.nan: None})

    results = []
    for _, row in top_5.iterrows():
        results.append({
            "id_site": str(row["id_site"]),
            "activity_type": str(row["activity_type"]),
            "recommendation_score": float(row["recommendation_score"])
        })

    return {
        "status": "success",
        "message": f"Đã ghi nhận tương tác với tài liệu {interaction.id_site}",
        "student_id": student_id,
        "recommendations": results
    }


# API 6: Template đọc Parquet tùy chỉnh
@app.get("/api/v1/template-data/{file_name}", summary="[Template GET] Mẫu API đọc file Parquet tùy chọn")
def get_custom_parquet_data(file_name: str):
    if not file_name.endswith(".parquet") or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="Tên tệp không hợp lệ. Chỉ chấp nhận các tệp .parquet trong thư mục serving.")
    df = get_cached(file_name)
    df = df.replace({np.nan: None})
    return {
        "file": file_name,
        "record_count": len(df),
        "data": df.head(50).to_dict(orient="records")
    }


# API 7: Xem trạng thái bộ nhớ cache
@app.get("/api/v1/cache/status", summary="Kiểm tra trạng thái bộ nhớ cache")
def get_cache_status():
    return {
        "cached_files": {
            fname: {"rows": len(df), "columns": list(df.columns)}
            for fname, df in _DATA_CACHE.items()
        },
        "total_files": len(_DATA_CACHE),
        "timestamp": datetime.utcnow().isoformat()
    }


# Health Check
@app.get("/health", summary="Health check endpoint")
def health_check():
    required_loaded = all(f in _DATA_CACHE for f in REQUIRED_FILES)
    return {
        "status": "healthy" if required_loaded else "degraded",
        "cache_ready": required_loaded,
        "cached_files": list(_DATA_CACHE.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }

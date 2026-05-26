import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(
    title="B-LEARN Big Data Serving API",
    description="REST API phục vụ dữ liệu Gold Layer (OULAD) cho ứng dụng React Web frontend",
    version="1.0.0"
)

# CORS middleware config: Allow cross-origin requests from React frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")

def load_serving_data(file_name: str) -> pd.DataFrame:
    try:
        if STORAGE_KEY:
            storage_options = {
                "account_name": STORAGE_ACCOUNT,
                "account_key": STORAGE_KEY
            }
            path = f"abfss://serving@{STORAGE_ACCOUNT}.dfs.core.windows.net/ui_data/{file_name}"
            return pd.read_parquet(path, storage_options=storage_options)
        else:
            # Fallback to public HTTP URL for local mock runs
            url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/serving/ui_data/{file_name}"
            return pd.read_parquet(url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi nạp dữ liệu Serving Layer ({file_name}): {str(e)}"
        )

# API 1: Trả về thống kê tổng quan (Cohort Stats) cho trang Dashboard chính
@app.get("/api/v1/cohort/stats", summary="Lấy thống kê tổng quan toàn trường (Demographics & Clicks)")
def get_cohort_stats():
    df = load_serving_data("cohort_stats.parquet")
    # Replace NaN values with None for clean JSON serialization
    df = df.replace({np.nan: None})
    return df.to_dict(orient="records")

# API 2: Trả về dự đoán rủi ro và độ thành thục kiến thức của 1 sinh viên
@app.get("/api/v1/student/{student_id}", summary="Lấy thông tin rủi ro & độ thành thục của học viên")
def get_student_profile(student_id: str):
    df_risk = load_serving_data("risk_predictions.parquet")
    df_bkt = load_serving_data("bkt_mastery.parquet")
    
    student_risk = df_risk[df_risk['student_id_hash'] == student_id]
    if student_risk.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy thông tin rủi ro cho học viên {student_id}")
        
    student_bkt = df_bkt[df_bkt['user_id'] == student_id]
    
    # Replace NaN with None
    risk_dict = student_risk.replace({np.nan: None}).to_dict(orient="records")[0]
    bkt_dict = student_bkt.replace({np.nan: None}).to_dict(orient="records")
    
    return {
        "student_id": student_id,
        "risk": risk_dict,
        "bkt_mastery": bkt_dict
    }

# API 3: Trả về Top 5 tài liệu được gợi ý cá nhân hóa dựa trên dot-product nhúng user/item
@app.get("/api/v1/student/{student_id}/recommendations", summary="Lấy top 5 gợi ý tài liệu học tập")
def get_student_recommendations(student_id: str):
    df_user_emb = load_serving_data("user_embeddings.parquet")
    df_item_emb = load_serving_data("item_embeddings.parquet")
    
    user_row = df_user_emb[df_user_emb['student_id_hash'] == student_id]
    if user_row.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ma trận nhúng của học viên {student_id}")
        
    u_emb = np.array(user_row.iloc[0]['user_embedding'])
    i_embs = np.stack(df_item_emb['item_embedding'].values)
    
    # Compute dot product
    scores = np.dot(i_embs, u_emb)
    df_scored = df_item_emb.copy()
    df_scored['recommendation_score'] = scores
    
    top_5 = df_scored.sort_values(by='recommendation_score', ascending=False).head(5)
    
    # Try to load VLE metadata to map activity type
    try:
        df_lms = load_serving_data("lms_simulator.parquet")
        top_5 = top_5.merge(df_lms, on="id_site", how="left")
    except Exception:
        # Fallback if lms_simulator.parquet is not exported/loaded yet
        top_5["activity_type"] = "resource"
        
    # Fill missing values
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

# API 4: Lấy danh sách các học viên (Student List)
@app.get("/api/v1/students", summary="Lấy danh sách các định danh học viên")
def get_student_list():
    df_risk = load_serving_data("risk_predictions.parquet")
    students = df_risk['student_id_hash'].unique().tolist()
    return {"students": students}

# Health Check API
@app.get("/health", summary="Health check endpoint")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

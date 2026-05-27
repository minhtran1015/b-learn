import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel

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

# Pydantic schema cho yêu cầu tương tác học viên
class StudentInteraction(BaseModel):
    id_site: str
    activity_type: str

# API 5: (Template POST) Gửi sự kiện tương tác của học viên & nhận gợi ý thích ứng lập tức
@app.post("/api/v1/student/{student_id}/interaction", summary="[Template POST] Gửi tương tác học viên & cập nhật gợi ý thời gian thực")
def record_interaction_and_recommend(student_id: str, interaction: StudentInteraction):
    """
    Mẫu API POST: Nhận sự kiện tương tác (Click tài liệu) từ React,
    giả lập dịch chuyển vector đặc trưng (user embedding) của học sinh đó
    và phản hồi lại danh sách gợi ý mới ngay lập tức.
    
    Đồng đội viết React có thể gọi API này để cập nhật đề xuất real-time khi học sinh học bài.
    """
    df_user_emb = load_serving_data("user_embeddings.parquet")
    df_item_emb = load_serving_data("item_embeddings.parquet")
    
    user_row = df_user_emb[df_user_emb['student_id_hash'] == student_id]
    if user_row.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ma trận nhúng của học viên {student_id}")
        
    u_emb = np.array(user_row.iloc[0]['user_embedding'])
    
    # Tìm item được tương tác để lấy vector nhúng
    # Thử tìm theo định dạng số hoặc chuỗi
    item_id_numeric = int(interaction.id_site) if interaction.id_site.isdigit() else None
    if item_id_numeric is not None:
        item_row = df_item_emb[df_item_emb['id_site'] == item_id_numeric]
    else:
        item_row = df_item_emb[df_item_emb['id_site'] == interaction.id_site]
        
    if not item_row.empty:
        i_emb = np.array(item_row.iloc[0]['item_embedding'])
        # Dịch chuyển vector học viên hướng về phía tài liệu học với hệ số alpha = 0.3
        u_emb = u_emb + 0.3 * i_emb
        
    i_embs = np.stack(df_item_emb['item_embedding'].values)
    scores = np.dot(i_embs, u_emb)
    
    df_scored = df_item_emb.copy()
    df_scored['recommendation_score'] = scores
    top_5 = df_scored.sort_values(by='recommendation_score', ascending=False).head(5)
    
    try:
        df_lms = load_serving_data("lms_simulator.parquet")
        top_5 = top_5.merge(df_lms, on="id_site", how="left")
    except Exception:
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

# API 6: (Template GET) Mẫu API lấy dữ liệu từ tệp Parquet tùy chỉnh
@app.get("/api/v1/template-data/{file_name}", summary="[Template GET] Mẫu API đọc file Parquet tùy chọn từ Serving Layer")
def get_custom_parquet_data(file_name: str):
    """
    Mẫu API GET: Chỉ cần truyền tên file (ví dụ: cohort_stats.parquet).
    Nó sẽ tự động đọc từ Azure Blob Storage hoặc fallback local và trả về JSON.
    Có thể copy mẫu này để mở thêm API cho các bảng dữ liệu mới trong tương lai.
    """
    # Tránh lỗ hổng bảo mật path traversal
    if not file_name.endswith(".parquet") or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="Tên tệp không hợp lệ. Chỉ chấp nhận các tệp .parquet trong thư mục serving.")
        
    df = load_serving_data(file_name)
    df = df.replace({np.nan: None})
    return {
        "file": file_name,
        "record_count": len(df),
        "data": df.head(50).to_dict(orient="records")  # Trả về tối đa 50 bản ghi làm ví dụ
    }

# Health Check API
@app.get("/health", summary="Health check endpoint")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


import os
import sys
import jwt
import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import pandas as pd
import numpy as np
from azure.storage.blob import ContainerClient
import io

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

storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

# Cache dữ liệu trong bộ nhớ để tránh I/O mạng liên tục
df_user_emb = None
df_item_emb = None
df_risk = None
last_loaded = None

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

def get_cached_data():
    global df_user_emb, df_item_emb, df_risk, last_loaded
    now = datetime.datetime.now()
    # Cache hết hạn sau 5 phút
    if last_loaded is None or (now - last_loaded).total_seconds() > 300:
        try:
            df_user_emb = load_parquet_file("user_embeddings.parquet")
            df_item_emb = load_parquet_file("item_embeddings.parquet")
            df_risk = load_parquet_file("risk_predictions.parquet")
            last_loaded = now
            print(f"[{now.isoformat()}] Dữ liệu phục vụ đã được làm mới thành công.")
        except Exception as e:
            print(f"Lỗi tải dữ liệu: {e}")
            if df_user_emb is None:
                # Mock dự phòng
                df_user_emb = pd.DataFrame()
                df_item_emb = pd.DataFrame()
                df_risk = pd.DataFrame()
    return df_user_emb, df_item_emb, df_risk

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
def login(username: str, role: str = "student"):
    """Tạo JWT access token. Demo chấp nhận mọi tài khoản hợp lệ."""
    access_token = create_access_token(
        data={"sub": username, "role": role},
        expires_delta=datetime.timedelta(hours=24)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/recommendations/{student_id_hash}")
def get_recommendations(student_id_hash: str, current_user: dict = Depends(verify_token)):
    """Tính toán RecSys realtime dựa trên vector nhúng LightGCN."""
    u_emb_df, i_emb_df, risk_df = get_cached_data()
    
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
    
    recs = []
    for idx, row in top_5.iterrows():
        recs.append({
            "id_site": int(row['id_site']),
            "score": float(row['score'])
        })
        
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

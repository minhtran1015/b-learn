import os
import streamlit as st
import pandas as pd
import numpy as np

# ─── PREMIUM MODERN DESIGN THEME (GLASSMORPHISM & CUSTOM TYPOGRAPHY) ───
st.set_page_config(
    page_title="B-LEARN: EdTech Analytics & Personalization",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Google Font & Glassmorphism styles
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Global font override */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Premium Headers */
    .main-title {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    /* Card containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease, border-color 0.3s ease;
        margin-bottom: 1.5rem;
    }
    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(77, 150, 255, 0.3);
    }
    
    /* Specific Status Indicators */
    .status-badge-safe {
        background: rgba(46, 213, 115, 0.2);
        color: #2ed573;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-risk {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-title">🎓 B-LEARN: Hệ Thống Phân Tích & Cá Nhân Hóa Học Tập (OULAD)</h1>', unsafe_allow_html=True)

# ─── SERVING LAYER CONNECTION ───
storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

@st.cache_data(ttl=3600)
def load_serving_data(file_name):
    if storage_key:
        storage_options = {
            "account_name": storage_account,
            "account_key": storage_key
        }
        path = f"abfss://serving@{storage_account}.dfs.core.windows.net/ui_data/{file_name}"
        return pd.read_parquet(path, storage_options=storage_options)
    else:
        # Fallback to HTTP for local mock runs
        url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data"
        return pd.read_parquet(f"{url}/{file_name}")

with st.spinner("⏳ Loading serving data vectors from Azure Cloud..."):
    try:
        df_risk = load_serving_data("risk_predictions.parquet")
        df_bkt = load_serving_data("bkt_mastery.parquet")
        df_user_emb = load_serving_data("user_embeddings.parquet")
        df_item_emb = load_serving_data("item_embeddings.parquet")
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu từ Serving Layer Cloud: {e}")
        st.stop()

# ─── SIDEBAR: BỘ LỌC TÌM KIẾM ĐÃ ĐƯỢC LÀM ĐẸP ───
st.sidebar.markdown(
    """
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="font-weight: 600; color: #4D96FF; margin: 0;">B-LEARN UI</h2>
        <span style="font-size: 0.85rem; color: #888;">Medallion Serving Console</span>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.header("🔍 Quản Lý Học Viên")
student_list = df_risk['student_id_hash'].unique()

# Tạo từ điển mapping để đánh số thứ tự Sinh viên cho dễ gọi tên khi demo
hash_to_friendly = {
    raw_hash: f"👤 Học viên #{idx+1} ({raw_hash[:8]}...)" 
    for idx, raw_hash in enumerate(student_list)
}

# Sử dụng format_func để hiển thị tên thân thiện lên Dropdown
selected_student = st.sidebar.selectbox(
    "Chọn học viên để phân tích:", 
    student_list, 
    format_func=lambda x: hash_to_friendly.get(x, x)
)

# Lọc dữ liệu riêng của sinh viên được chọn
student_risk_rows = df_risk[df_risk['student_id_hash'] == selected_student]
if student_risk_rows.empty:
    st.warning("Không tìm thấy thông tin rủi ro cho sinh viên này.")
    st.stop()
student_risk = student_risk_rows.iloc[0]

# BKT uses user_id as identifier (string type matching)
student_bkt = df_bkt[df_bkt['user_id'] == str(selected_student)]

# Hiển thị profile góc trên cùng của Dashboard
st.subheader(f"📊 Hồ sơ phân tích: Học viên #{list(student_list).index(selected_student) + 1}")
st.info(f"🔑 Định danh bảo mật (SHA-256 Cloud ID): `{selected_student}`")

# ─── VIEW 1: CẢNH BÁO RỦI RO (LIGHTGBM) ───
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("🚨 Phân Tích Nguy Cơ Bỏ Học & Kết Quả (LightGBM)")
col1, col2, col3 = st.columns(3)
with col1:
    prob = student_risk.get('dropout_probability', 0.15)
    st.metric(label="Xác suất bỏ học", value=f"{prob*100:.2f}%")
with col2:
    status_html = (
        '<span class="status-badge-risk">🔴 Nguy cơ cao</span>'
        if prob > 0.5 else
        '<span class="status-badge-safe">🟢 An toàn</span>'
    )
    st.markdown(f"**Trạng thái hệ thống:** {status_html}", unsafe_allow_html=True)
with col3:
    pred_class = student_risk.get('predicted_class', 'Success')
    st.metric(label="Dự đoán kết quả cuối kỳ", value=pred_class)
st.markdown('</div>', unsafe_allow_html=True)

# ─── VIEW 2: LỖ HỔNG KIẾN THỨC (pyBKT) ───
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("🧠 Biểu Đồ Thành Thục Kiến Thức (Bayesian Knowledge Tracing)")
if not student_bkt.empty:
    # Build a clean dataframe for display
    display_bkt = student_bkt[['skill_name', 'correct_predictions']].copy()
    display_bkt = display_bkt.rename(
        columns={
            'skill_name': 'Kỹ năng / Phân mục học tập (Skill Name)',
            'correct_predictions': 'Độ thành thục kiến thức (Mastery State)'
        }
    )
    # Style the percentage representation
    display_bkt['Độ thành thục kiến thức (Mastery State)'] = display_bkt['Độ thành thục kiến thức (Mastery State)'].apply(lambda x: f"{x*100:.1f}%")
    st.dataframe(display_bkt, use_container_width=True)
else:
    st.info("Sinh viên này chưa thực hiện bài tập chuỗi tuần tự tuần này.")
st.markdown('</div>', unsafe_allow_html=True)

# ─── VIEW 3: GỢI Ý TÀI LIỆU CÁ NHÂN HÓA REAL-TIME (LIGHTGCN) ───
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.subheader("🎯 Gợi Ý Tài Liệu Học Tập Phù Hợp (LightGCN Đồ Thị Deep Learning)")

# Lấy Vector Nhúng của sinh viên hiện tại
user_row = df_user_emb[df_user_emb['student_id_hash'] == selected_student]
if not user_row.empty:
    u_emb = np.array(user_row.iloc[0]['user_embedding'])
    
    # Lấy toàn bộ ma trận nhúng của tài liệu
    i_embs = np.stack(df_item_emb['item_embedding'].values)
    
    # Tính Dot-Product cực nhanh trên CPU bằng Numpy để ra điểm tương đồng
    scores = np.dot(i_embs, u_emb)
    df_item_emb_scored = df_item_emb.copy()
    df_item_emb_scored['recommendation_score'] = scores
    
    # Lấy Top 5 tài liệu có điểm cao nhất để gợi ý cho sinh viên
    top_5_items = df_item_emb_scored.sort_values(by='recommendation_score', ascending=False).head(5)
    st.success("Hệ thống khuyên dùng 5 tài liệu học tập sau đây để bù đắp kiến thức:")
    
    # Format scores for clean viewing
    top_5_items['recommendation_score'] = top_5_items['recommendation_score'].apply(lambda x: f"{x:.4f}")
    
    st.dataframe(
        top_5_items[['id_site', 'recommendation_score']].rename(
            columns={
                'id_site': 'Mã tài liệu trên LMS (VLE Site ID)',
                'recommendation_score': 'Độ phù hợp cá nhân hóa (RecSys Score)'
            }
        ),
        use_container_width=True
    )
else:
    st.warning("Không tìm thấy dữ liệu Vector nhúng cho sinh viên này.")
st.markdown('</div>', unsafe_allow_html=True)

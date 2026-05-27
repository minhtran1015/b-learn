import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from azure.storage.blob import ContainerClient
import io

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
    
    /* Thẻ CSS an toàn, chỉ áp dụng cho khung viền mặc định của Streamlit */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.6) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 1rem;
    }

    /* Đảm bảo màu chữ hiển thị rõ ràng trên nền sáng */
    h1, h2, h3, h4, h5, h6, p, label {
        color: #1e1e24 !important;
    }

    /* Đảm bảo console log không bị ghi đè màu chữ */
    .console-log * {
        color: inherit !important;
    }

    /* Giữ kiểu dáng cho class glass-card tự chế */
    .glass-card {
        background: rgba(255, 255, 255, 0.6) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 1rem;
        padding: 1.5rem;
    }
    
    /* Specific Status Indicators */
    .status-badge-safe {
        background: rgba(46, 213, 115, 0.2);
        color: #2ed573 !important;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-risk {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757 !important;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Console-style logs */
    .console-log {
        background-color: #1e1e24;
        color: #7bed9f;
        font-family: 'Courier New', Courier, monospace;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        border-left: 4px solid #2ed573;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-title">🎓 B-LEARN: Hệ Thống Phân Tích & Cá Nhân Hóa Học Tập (OULAD)</h1>', unsafe_allow_html=True)

# ─── SERVING LAYER CONNECTION ───
storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

# @st.cache_data: correct decorator for DataFrames — hashes arguments, serializes
# return value to disk, safe for multi-user Streamlit. ttl=7200 = 2h refresh.
@st.cache_data(ttl=3600, show_spinner=False)
def load_serving_data(file_name):
    """Load a Parquet file from Azure Blob Storage using fast flat HTTPS streaming client."""
    t0 = datetime.now()
    if storage_key:
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
                if b.name.endswith(".parquet") and b.size > 0:
                    stream = io.BytesIO()
                    container_client.get_blob_client(b.name).download_blob().readinto(stream)
                    stream.seek(0)
                    dfs.append(pd.read_parquet(stream))
            
            if not dfs:
                raise FileNotFoundError(f"No parquet files found in {prefix}")
            df = pd.concat(dfs, ignore_index=True)
        except Exception as e:
            # Fallback to direct HTTP URL read if SDK call fails
            url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data"
            df = pd.read_parquet(f"{url}/{file_name}")
    else:
        url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data"
        df = pd.read_parquet(f"{url}/{file_name}")
    
    elapsed = (datetime.now() - t0).total_seconds()
    print(f"[CACHE] Loaded {file_name}: {len(df)} rows in {elapsed:.2f}s")
    return df


@st.cache_data(ttl=3600)
def precompute_cohort_metrics(_df_risk, _df_bkt):
    total_students = len(_df_risk['student_id_hash'].unique())
    avg_risk = _df_risk['dropout_probability'].mean() * 100
    
    stuck_skill_name = "N/A"
    stuck_skill_val = 0.0
    if not _df_bkt.empty:
        try:
            _df_bkt_clean = _df_bkt.copy()
            _df_bkt_clean['correct_predictions'] = _df_bkt_clean['correct_predictions'].astype(float)
            skill_averages = _df_bkt_clean.groupby('skill_name')['correct_predictions'].mean().reset_index()
            if not skill_averages.empty:
                lowest_skill = skill_averages.sort_values(by='correct_predictions').iloc[0]
                stuck_skill_name = lowest_skill['skill_name']
                stuck_skill_val = lowest_skill['correct_predictions']
        except Exception:
            pass
            
    return total_students, avg_risk, stuck_skill_name, stuck_skill_val


@st.cache_data(ttl=3600)
def generate_curated_student_list(_df_risk):
    # TỐI ƯU CỐT LÕI: Trích xuất ra danh sách rút gọn gồm 25 sinh viên rủi ro nhất 
    # và 25 sinh viên an toàn nhất để demo mượt mà, tránh nhét 25k dòng làm sập DOM trình duyệt
    top_at_risk = _df_risk.sort_values(by='dropout_probability', ascending=False).head(25)
    top_safe = _df_risk.sort_values(by='dropout_probability', ascending=True).head(25)
    curated_df = pd.concat([top_at_risk, top_safe]).drop_duplicates(subset=['student_id_hash'])
    return curated_df['student_id_hash'].tolist()

with st.spinner("⏳ Đang nạp dữ liệu từ Azure Cloud (lần đầu mất ~10-15s, sau đó phục vụ từ bộ nhớ)..."):
    try:
        df_risk = load_serving_data("risk_predictions.parquet")
        df_bkt = load_serving_data("bkt_mastery.parquet")
        df_user_emb = load_serving_data("user_embeddings.parquet")
        df_item_emb = load_serving_data("item_embeddings.parquet")
        
        # Load descriptive stats with local mock fallback
        try:
            df_cohort = load_serving_data("cohort_stats.parquet")
        except Exception as e:
            df_cohort = pd.DataFrame([
                {"metric_name": "gender", "category": "M", "value": None, "count": 1500},
                {"metric_name": "gender", "category": "F", "value": None, "count": 1300},
                {"metric_name": "highest_education", "category": "HE Qualification", "value": None, "count": 800},
                {"metric_name": "highest_education", "category": "A Level or Equivalent", "value": None, "count": 1200},
                {"metric_name": "highest_education", "category": "Lower Than A Level", "value": None, "count": 800},
                {"metric_name": "region", "category": "London Region", "value": None, "count": 600},
                {"metric_name": "region", "category": "South Region", "value": None, "count": 700},
                {"metric_name": "region", "category": "North Region", "value": None, "count": 500},
                {"metric_name": "region", "category": "Wales", "value": None, "count": 400},
                {"metric_name": "region", "category": "Scotland", "value": None, "count": 600},
                {"metric_name": "engagement_weekly", "category": "0", "value": 15.2, "count": None},
                {"metric_name": "engagement_weekly", "category": "1", "value": 18.5, "count": None},
                {"metric_name": "engagement_weekly", "category": "2", "value": 22.1, "count": None},
                {"metric_name": "engagement_weekly", "category": "3", "value": 19.8, "count": None},
                {"metric_name": "engagement_weekly", "category": "4", "value": 24.3, "count": None},
            ])
            
        # Load VLE metadata with local fallback
        try:
            df_lms = load_serving_data("lms_simulator.parquet")
        except Exception as e:
            df_lms = pd.DataFrame({
                "id_site": df_item_emb["id_site"].unique().astype(int),
                "activity_type": np.random.choice(["oucontent", "forumng", "url", "resource", "subpage", "quiz"], size=len(df_item_emb["id_site"].unique()))
            })
    except Exception as e:
        st.error(f"Lỗi nạp dữ liệu từ Serving Layer Cloud: {e}")
        st.stop()

# Helper function to get activity type for VLE sites
def get_vle_activity(site_id):
    try:
        val = int(site_id)
        row = df_lms[df_lms['id_site'] == val]
        if not row.empty:
            return str(row.iloc[0]['activity_type'])
    except Exception:
        pass
    return "resource"

# Helper for nice icons
def get_activity_icon(activity_type):
    icons = {
        "oucontent": "📖",
        "forumng": "💬",
        "url": "🔗",
        "resource": "📄",
        "subpage": "📄",
        "quiz": "📝",
        "homepage": "🏠"
    }
    return icons.get(activity_type, "📄")

@st.cache_data(show_spinner=False)
def compute_recommendations(student_id_hash: str):
    """Cache dot-product scoring per student_id_hash (recomputed only on student change)."""
    try:
        _user_emb = load_serving_data("user_embeddings.parquet")
        _item_emb = load_serving_data("item_embeddings.parquet")
        user_row = _user_emb[_user_emb['student_id_hash'] == student_id_hash]
        if user_row.empty:
            return None
        u_emb = np.array(user_row.iloc[0]['user_embedding'])
        i_embs = np.stack(_item_emb['item_embedding'].values)
        scores = np.dot(i_embs, u_emb)
        df_scored = _item_emb.copy()
        df_scored['recommendation_score'] = scores
        return df_scored.sort_values(by='recommendation_score', ascending=False).head(5).copy()
    except Exception:
        return None


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
st.sidebar.header("🔑 Quyền hạn truy cập")
is_admin = st.sidebar.toggle("🔓 Chế độ Giảng viên (Hiện danh tính thực)", value=False)

st.sidebar.header("🔍 Quản Lý Học Viên")

# Lấy danh sách 50 học viên tiêu biểu đã được cache tăng tốc
curated_student_list = generate_curated_student_list(df_risk)

# Đảm bảo cột id_student luôn tồn tại
# IMPORTANT: copy() trước khi mutation — df_risk từ cache_data là immutable
df_risk = df_risk.copy()
if 'id_student' not in df_risk.columns:
    import hashlib
    # Sinh MSSV giả định dài 6 chữ số dựa trên hash của sinh viên để ổn định khi thay đổi trang
    def get_stable_fake_id(h):
        return str(int(hashlib.md5(h.encode('utf-8')).hexdigest()[:6], 16) % 900000 + 100000)
    df_risk['id_student'] = df_risk['student_id_hash'].apply(get_stable_fake_id)

# Tạo từ điển mapping để hiển thị danh sách thân thiện hoặc giải mã MSSV thực tế
hash_to_friendly = {}
for idx, raw_hash in enumerate(curated_student_list):
    row_data = df_risk[df_risk['student_id_hash'] == raw_hash]
    if is_admin and not row_data.empty:
        real_id = row_data.iloc[0]['id_student']
        hash_to_friendly[raw_hash] = f"👤 MSSV: {real_id} (#{idx+1})"
    else:
        hash_to_friendly[raw_hash] = f"👤 Học viên #{idx+1} ({raw_hash[:8]}...)"

# Công tắc chọn phương thức tìm kiếm để linh hoạt khi chấm điểm
search_mode = st.sidebar.radio("Chế độ chọn:", ["Chọn từ danh sách tiêu biểu", "Nhập mã Cloud ID thủ công"])

if search_mode == "Chọn từ danh sách tiêu biểu":
    selected_student = st.sidebar.selectbox(
        "Chọn học viên mẫu (Top Risk/Safe):", 
        curated_student_list, 
        format_func=lambda x: hash_to_friendly.get(x, x)
    )
else:
    search_input = st.sidebar.text_input("Dán mã SHA-256 Cloud ID của sinh viên vào đây:")
    if search_input:
        selected_student = search_input.strip()
    else:
        selected_student = curated_student_list[0] # Mặc định lấy người đầu tiên nếu để trống


# Lọc dữ liệu riêng của sinh viên được chọn
student_risk_rows = df_risk[df_risk['student_id_hash'] == selected_student]
if student_risk_rows.empty:
    st.warning("Không tìm thấy thông tin rủi ro cho sinh viên này.")
    st.stop()
student_risk = student_risk_rows.iloc[0]

# BKT uses user_id as identifier (string type matching)
student_bkt = df_bkt[df_bkt['user_id'] == str(selected_student)]

# Initialize session state for embedding simulation
if 'current_student' not in st.session_state or st.session_state.current_student != selected_student:
    st.session_state.current_student = selected_student
    user_row = df_user_emb[df_user_emb['student_id_hash'] == selected_student]
    if not user_row.empty:
        st.session_state.custom_u_emb = np.array(user_row.iloc[0]['user_embedding'])
    else:
        st.session_state.custom_u_emb = None
    st.session_state.interactions_log = []

# ─── TẠO TABS GIAO DIỆN ───
tab1, tab2, tab3 = st.tabs([
    "📈 Tổng Quan Toàn Trường (Cohort Analytics)",
    "👤 Hồ Sơ Cá Nhân Hóa (Student Deep-Dive)",
    "🎮 Giả Lập Tương Tác LMS (External App Integration)"
])

# ==========================================
# TAB 1: COHORT ANALYTICS
# ==========================================
with tab1:
    st.subheader("📈 Phân tích chỉ số tổng quan & Nhân khẩu học học đường")
    
    # Compute cohort-level metrics using cached function
    total_students, avg_risk, stuck_skill_name, stuck_skill_val = precompute_cohort_metrics(df_risk, df_bkt)

    # Render beautiful KPI cards
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Tổng Học Viên Quản Lý</div>
                <div style="font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #FF6B6B 0%, #4D96FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total_students:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_kpi2:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Tỷ Lệ Bỏ Học Trung Bình (LightGBM)</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #ff4757;">{avg_risk:.2f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_kpi3:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Kỹ Năng Gây Kẹt Nhất (pyBKT)</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #ffa502; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{stuck_skill_name}">{stuck_skill_name} <span style="font-size: 1.1rem; font-weight: 500;">({stuck_skill_val*100:.1f}%)</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Pie chart: Gender
        df_gender = df_cohort[df_cohort["metric_name"] == "gender"]
        if not df_gender.empty:
            fig_gender = px.pie(
                df_gender, 
                names="category", 
                values="count", 
                title="Phân phối giới tính của Cohort (Gender Distribution)",
                hole=0.4,
                color_discrete_sequence=["#FF6B6B", "#4D96FF"]
            )
            fig_gender.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#ffffff"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            with st.container(border=True):
                st.plotly_chart(fig_gender, use_container_width=True)

        # Bar chart: Education
        df_edu = df_cohort[df_cohort["metric_name"] == "highest_education"]
        if not df_edu.empty:
            fig_edu = px.bar(
                df_edu,
                x="count",
                y="category",
                orientation="h",
                title="Trình độ học vấn của Cohort (Highest Education)",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_edu.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#ffffff"),
                showlegend=False,
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=None)
            )
            with st.container(border=True):
                st.plotly_chart(fig_edu, use_container_width=True)

    with col_chart2:
        # Bar chart: Region
        df_region = df_cohort[df_cohort["metric_name"] == "region"].sort_values(by="count", ascending=False).head(8)
        if not df_region.empty:
            fig_region = px.bar(
                df_region,
                x="count",
                y="category",
                orientation="h",
                title="Phân bố vùng miền Cohort (Top 8 Regions)",
                color="count",
                color_continuous_scale="Viridis"
            )
            fig_region.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit", color="#ffffff"),
                coloraxis_showscale=False,
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=None)
            )
            with st.container(border=True):
                st.plotly_chart(fig_region, use_container_width=True)

        # Line chart: Engagement trend
        df_trend = df_cohort[df_cohort["metric_name"] == "engagement_weekly"].copy()
        if not df_trend.empty:
            try:
                df_trend["category"] = df_trend["category"].astype(int)
                df_trend = df_trend.sort_values(by="category")
                fig_trend = px.line(
                    df_trend,
                    x="category",
                    y="value",
                    title="Xu hướng click chuột trung bình qua các tuần học (Cohort Baseline)",
                    labels={"category": "Tuần học (Week)", "value": "Lượt click trung bình / học viên"},
                    markers=True
                )
                fig_trend.update_traces(line_color="#4D96FF", line_width=3, marker=dict(size=8, color="#FF6B6B"))
                fig_trend.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Outfit", color="#ffffff"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", dtick=1),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                with st.container(border=True):
                    st.plotly_chart(fig_trend, use_container_width=True)
            except Exception:
                pass

# ==========================================
# TAB 2: STUDENT DEEP-DIVE (BẢN GỐC LÀM ĐẸP)
# ==========================================
with tab2:
    st.subheader(f"📊 Hồ sơ cá nhân học tập: {hash_to_friendly.get(selected_student, f'👤 Học viên ({selected_student[:8]}...)')}")
    st.info(f"🔑 Định danh bảo mật (SHA-256 Cloud ID): `{selected_student}`")

    # ─── VIEW 1: CẢNH BÁO RỦI RO (LIGHTGBM) ───
    with st.container(border=True):
        st.markdown("<h3 style='margin:0 0 1rem 0;'>🚨 Phân Tích Nguy Cơ Bỏ Học & Kết Quả (LightGBM)</h3>", unsafe_allow_html=True)
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

    # ─── VIEW 2: LỖ HỔNG KIẾN THỨC (pyBKT) ───
    with st.container(border=True):
        st.markdown("<h3 style='margin:0 0 1rem 0;'>🧠 Biểu Đồ Thành Thục Kiến Thức (Bayesian Knowledge Tracing)</h3>", unsafe_allow_html=True)
        if not student_bkt.empty:
            display_bkt = student_bkt[['skill_name', 'correct_predictions']].copy()
            display_bkt = display_bkt.rename(
                columns={
                    'skill_name': 'Kỹ năng / Phân mục học tập (Skill Name)',
                    'correct_predictions': 'Độ thành thục kiến thức (Mastery State)'
                }
            )
            # Style the percentage representation safely
            try:
                display_bkt['Độ thành thục kiến thức (Mastery State)'] = display_bkt['Độ thành thục kiến thức (Mastery State)'].astype(float).apply(lambda x: f"{x*100:.1f}%")
            except Exception:
                pass
            st.dataframe(display_bkt, use_container_width=True)
        else:
            st.info("Sinh viên này chưa thực hiện bài tập chuỗi tuần tự tuần này.")

    # ─── VIEW 3: GỢI Ý TÀI LIỆU CÁ NHÂN HÓA (LIGHTGCN) ───
    with st.container(border=True):
        st.markdown("<h3 style='margin:0 0 1rem 0;'>🎯 Gợi Ý Tài Liệu Học Tập Phù Hợp (LightGCN Đồ Thị Deep Learning)</h3>", unsafe_allow_html=True)
        
        # Use cached recommendations; fall back to session_state only for NRT embedding shifts
        if st.session_state.get('interactions_log'):  # User has done NRT interactions
            top_5_items = None
            if st.session_state.custom_u_emb is not None:
                u_emb = st.session_state.custom_u_emb
                i_embs = np.stack(df_item_emb['item_embedding'].values)
                scores = np.dot(i_embs, u_emb)
                df_item_emb_scored = df_item_emb.copy()
                df_item_emb_scored['recommendation_score'] = scores
                top_5_items = df_item_emb_scored.sort_values(by='recommendation_score', ascending=False).head(5).copy()
        else:
            # ⚡ Use cached dot-product — instant for already-viewed students
            top_5_items = compute_recommendations(selected_student)
    
        if top_5_items is not None:
            st.success("Hệ thống khuyên dùng 5 tài liệu học tập sau đây để bù đắp kiến thức:")
            top_5_items = top_5_items.copy()
            top_5_items['recommendation_score'] = top_5_items['recommendation_score'].apply(lambda x: f"{x:.4f}")
            top_5_items['activity_type'] = top_5_items['id_site'].apply(get_vle_activity)
            top_5_items['display_activity'] = top_5_items['activity_type'].apply(lambda x: f"{get_activity_icon(x)} {x}")
            st.dataframe(
                top_5_items[['id_site', 'display_activity', 'recommendation_score']].rename(
                    columns={
                        'id_site': 'Mã tài liệu (VLE Site ID)',
                        'display_activity': 'Phân loại học liệu (Type)',
                        'recommendation_score': 'Độ phù hợp cá nhân hóa (Score)'
                    }
                ),
                use_container_width=True
            )
        else:
            st.warning("Không tìm thấy dữ liệu Vector nhúng cho sinh viên này.")


# ==========================================
# TAB 3: EXTERNAL LMS WEB DEMO
# ==========================================
with tab3:
    st.subheader("🎮 Giả lập ứng dụng LMS bên thứ ba & Thích ứng thời gian thực (NRT)")
    
    st.markdown(
        """
        <div class="glass-card" style="margin-bottom: 2rem;">
            <h4>🏫 Cổng Thông Tin Học Tập Sinh Viên (LMS Portal Simulator)</h4>
            <p style="color: #bbb; font-size: 0.9rem;">
                Mô phỏng hành vi của sinh viên khi tương tác với giao diện học trực tuyến. 
                Khi sinh viên bấm đọc một học liệu bên dưới, Streamlit sẽ mô phỏng việc sinh viên phát sinh Clickstream ghi vào Silver Layer, 
                tự động kích hoạt <strong>NRT Gold Inference</strong> cập nhật Vector nhúng của sinh viên và ngay lập tức thay đổi danh sách gợi ý học tập tiếp theo.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_lms_left, col_lms_right = st.columns([7, 5])
    
    with col_lms_left:
        st.markdown("##### 📖 Danh sách học liệu hệ thống đề xuất học tập:")
        
        # We fetch recommendations list to show as interactive buttons
        if st.session_state.custom_u_emb is not None:
            u_emb = st.session_state.custom_u_emb
            i_embs = np.stack(df_item_emb['item_embedding'].values)
            scores = np.dot(i_embs, u_emb)
            
            df_item_emb_scored = df_item_emb.copy()
            df_item_emb_scored['recommendation_score'] = scores
            top_5_items = df_item_emb_scored.sort_values(by='recommendation_score', ascending=False).head(5).copy()
            
            for idx, row in top_5_items.iterrows():
                site_id = row['id_site']
                act_type = get_vle_activity(site_id)
                icon = get_activity_icon(act_type)
                
                # Render study buttons
                btn_label = f"{icon} Đọc tài liệu: VLE SITE ID #{site_id} ({act_type})"
                if st.button(btn_label, key=f"study_btn_{site_id}"):
                    # Update student vector embedding in-memory: u_new = u_old + 0.3 * item_embedding
                    item_row = df_item_emb[df_item_emb['id_site'] == str(site_id)]
                    if not item_row.empty:
                        i_emb = np.array(item_row.iloc[0]['item_embedding'])
                        # Perturbation shift
                        new_vec = st.session_state.custom_u_emb + 0.3 * i_emb
                        st.session_state.custom_u_emb = new_vec / np.linalg.norm(new_vec)
                        
                        # Log the events
                        t_now = datetime.now().strftime('%H:%M:%S')
                        student_disp = df_risk[df_risk['student_id_hash'] == selected_student].iloc[0]['id_student'] if is_admin else f"{selected_student[:8]}..."
                        st.session_state.interactions_log.append(f"🟢 [{t_now}] [Bronze/Silver] Clickstream logged: student={student_disp}, site_id={site_id}")
                        st.session_state.interactions_log.append(f"⚙️ [{t_now}] [Gold NRT] Triggered online embedding update: Vector shifted toward site_id={site_id}")
                        st.session_state.interactions_log.append(f"🔄 [{t_now}] [Serving] Refreshed recommendations cache locally")

                        
                        st.success(f"Đã ghi nhận tương tác với tài liệu #{site_id}! Trạng thái cá nhân hóa đã được cập nhật.")
                        st.rerun()
        else:
            st.warning("Không tìm thấy dữ liệu Vector nhúng cho sinh viên này.")

    with col_lms_right:
        st.markdown("##### 📝 Nhật ký tương tác & Xử lý Near-Real-Time (NRT):")
        
        if st.session_state.interactions_log:
            log_content = "<br>".join(st.session_state.interactions_log[::-1]) # Show newest first
            st.markdown(
                f"""
                <div class="console-log">
                    {log_content}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="console-log" style="border-left-color: #ff4757; color: #ff7675;">
                    [Chưa có tương tác nào được thực hiện trong phiên này]
                </div>
                """,
                unsafe_allow_html=True
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Khôi phục ban đầu (Reset Session)"):
            st.session_state.current_student = None
            st.rerun()


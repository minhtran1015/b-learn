import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import datetime as dt
from azure.storage.blob import ContainerClient
import io
import requests
import jwt

# ─── PREMIUM MODERN DESIGN THEME (GLASSMORPHISM & CUSTOM TYPOGRAPHY) ───
st.set_page_config(
    page_title="B-LEARN: EdTech Analytics & Personalization",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Google Font & Glassmorphism styles matching style.css exactly
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Global font override */
    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #f8fafc !important;
    }
    
    /* Background style override for streamlit elements */
    .stApp {
        background-color: #0f172a;
    }
    
    /* Glassmorphic card styling matching style.css */
    .glass-card {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Specific Status Indicators */
    .status-badge-safe {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981 !important;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-risk {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444 !important;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Console-style logs */
    .console-log {
        background-color: #0f172a;
        color: #10b981;
        font-family: 'Courier New', Courier, monospace;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        border-left: 4px solid #10b981;
        margin-top: 1rem;
        max-height: 300px;
        overflow-y: auto;
    }
    
    /* Sidebar styling overrides */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Field labels */
    .field-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar footer */
    .sidebar-footer {
        margin-top: 2rem;
        font-size: 0.85rem;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .status-indicator.online {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── SERVING LAYER CONNECTION ───
storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "b-learn-super-secret-key-1015")

def get_auth_token():
    payload = {
        "sub": "admin_dashboard",
        "role": "admin",
        "exp": datetime.utcnow() + dt.timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

def fetch_student_profile_from_gateway(student_id_hash: str) -> dict:
    """Fetch live recommendations, BKT mastery, and dropout probability from FastAPI gateway."""
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{GATEWAY_URL}/recommendations/{student_id_hash}"
        response = requests.get(url, headers=headers, timeout=2.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching live data from gateway: {e}")
    return None

def send_kafka_event(student_id_hash: str, id_site: int, activity_type: str = "") -> tuple[bool, str]:
    """Send a click event to the FastAPI Serving Gateway's `/track-click` endpoint."""
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "student_id_hash": student_id_hash,
            "id_site": int(id_site),
            "code_module": "AAA",
            "code_presentation": "2014J",
            "sum_click": 1,
            "event_type": "click",
            "page_path": f"/material/{id_site}",
            "source": "streamlit-dashboard"
        }
        url = f"{GATEWAY_URL}/track-click"
        response = requests.post(url, json=payload, headers=headers, timeout=2.0)
        if response.status_code == 200:
            return True, f"Status {response.status_code}: click tracked"
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def send_assessment_submission(student_id_hash: str, assignment_id: str, score: float) -> tuple[bool, str]:
    """Send an assignment submission score to the FastAPI Serving Gateway's `/submit-assessment` endpoint."""
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "student_id_hash": student_id_hash,
            "assignment_id": str(assignment_id),
            "score": float(score)
        }
        url = f"{GATEWAY_URL}/submit-assessment"
        response = requests.post(url, json=payload, headers=headers, timeout=2.0)
        if response.status_code == 200:
            return True, f"Status {response.status_code}: {response.json().get('message', 'assessment tracked')}"
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def reset_gateway_demo_state() -> tuple[bool, str]:
    """Reset the demo state on the Serving Gateway using `/reset-assessment-shifts`."""
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{GATEWAY_URL}/reset-assessment-shifts"
        response = requests.post(url, headers=headers, timeout=2.0)
        if response.status_code == 200:
            return True, "Demo state successfully reset on Serving Gateway."
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

@st.cache_data(ttl=3600, show_spinner=False)
def load_serving_data(file_name):
    """Load a Parquet file using local Pod-Disk cache (Local File Mirroring) to prevent network I/O hangs."""
    t0 = datetime.now()
    local_cache_path = f"/tmp/{file_name}"
    
    if not storage_key:
        url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data/{file_name}"
        df = pd.read_parquet(url)
        elapsed = (datetime.now() - t0).total_seconds()
        print(f"[LOCAL MOCK] Loaded {file_name}: {len(df)} rows in {elapsed:.2f}s")
        return df
        
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
        except Exception as e:
            url = f"https://{storage_account}.blob.core.windows.net/serving/ui_data"
            df = pd.read_parquet(f"{url}/{file_name}")
            df.to_parquet(local_cache_path)
                
    if os.path.exists(local_cache_path):
        df = pd.read_parquet(local_cache_path)
        elapsed = (datetime.now() - t0).total_seconds()
        print(f"[DISK-CACHE] Loaded {file_name}: {len(df)} rows in {elapsed:.2f}s")
        return df
    else:
        raise FileNotFoundError(f"Không thể khởi tạo bản sao dữ liệu cho {file_name}")

@st.cache_data(ttl=60)
def generate_curated_student_list(_df_risk):
    # Extract top 25 high risk and top 25 low risk students for smooth select list
    top_at_risk = _df_risk.sort_values(by='dropout_probability', ascending=False).head(25)
    top_safe = _df_risk.sort_values(by='dropout_probability', ascending=True).head(25)
    curated_df = pd.concat([top_at_risk, top_safe]).drop_duplicates(subset=['student_id_hash'])
    return curated_df['student_id_hash'].tolist()

@st.cache_data(ttl=60)
def get_student_timeline_data(student_id, base_prob):
    try:
        seed_val = int(student_id[:6], 16) % 1000
    except ValueError:
        import hashlib
        seed_val = int(hashlib.md5(student_id.encode('utf-8')).hexdigest()[:6], 16) % 1000
        
    np.random.seed(seed_val)
    trend_factor = 1.1 if base_prob > 0.5 else 0.8
    
    timeline_records = []
    checkpoints = ["Tuần 4", "Tuần 8", "Tuần 12", "Tuần 16"]
    cohort_baselines_risk = [22.4, 28.1, 32.5, 30.2]
    cohort_baselines_bkt = [45.0, 58.2, 65.4, 72.1]
    
    current_risk = base_prob
    current_bkt = 40.0 + np.random.randint(-10, 15)
    
    for i, cp in enumerate(checkpoints):
        current_risk = min(max(current_risk * (trend_factor + np.random.uniform(-0.1, 0.15)), 0.02), 0.98)
        current_bkt = min(max(current_bkt + np.random.uniform(2, 12) * (1.5 if trend_factor < 1 else 0.5), 5.0), 98.5)
        
        timeline_records.append({
            "Mốc thời gian": cp,
            "Xác suất bỏ học (%)": round(current_risk * 100, 2),
            "Trường học (Risk Baseline) (%)": cohort_baselines_risk[i],
            "Độ thành thục BKT (%)": round(current_bkt, 2),
            "Trường học (BKT Baseline) (%)": cohort_baselines_bkt[i]
        })
    df_timeline = pd.DataFrame(timeline_records)
    
    checkpoint_order = ["Tuần 4", "Tuần 8", "Tuần 12", "Tuần 16"]
    df_timeline["Mốc thời gian"] = pd.Categorical(
        df_timeline["Mốc thời gian"], 
        categories=checkpoint_order, 
        ordered=True
    )
    df_timeline = df_timeline.sort_values(by="Mốc thời gian")
    return df_timeline

# Helper function to get activity type for VLE sites
def get_vle_activity(site_id, df_lms):
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

# ─── SIDEBAR: GLOBAL FILTERS (Wireframe Theme) ───
st.sidebar.markdown(
    """
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #3b82f6; font-size: 1.5rem; font-weight: bold; margin: 0;">🎓 B-LEARN</h2>
        <span style="font-size: 0.8rem; color: #94a3b8;">EdTech Analytics Platform</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Load data with local caching
with st.spinner("⏳ Loading serving data..."):
    try:
        df_risk = load_serving_data("risk_predictions.parquet")
        df_bkt = load_serving_data("bkt_mastery.parquet")
        df_user_emb = load_serving_data("user_embeddings.parquet")
        df_item_emb = load_serving_data("item_embeddings.parquet")
        
        try:
            df_cohort = load_serving_data("cohort_stats.parquet")
        except Exception:
            df_cohort = pd.DataFrame()
            
        try:
            df_lms = load_serving_data("lms_simulator.parquet")
        except Exception:
            df_lms = pd.DataFrame({
                "id_site": df_item_emb["id_site"].unique().astype(int),
                "activity_type": np.random.choice(["oucontent", "forumng", "url", "resource", "subpage", "quiz"], size=len(df_item_emb["id_site"].unique()))
            })
    except Exception as e:
        st.error(f"Error loading serving layer: {e}")
        st.stop()

# Ensure standard columns are available
if 'id_student' not in df_risk.columns:
    import hashlib
    df_risk['id_student'] = df_risk['student_id_hash'].apply(lambda h: str(int(hashlib.md5(h.encode('utf-8')).hexdigest()[:6], 16) % 900000 + 100000))

# Chọn Khóa Học
st.sidebar.markdown('<div class="field-label">Chọn Khóa Học</div>', unsafe_allow_html=True)
unique_modules = sorted(df_risk['code_module'].unique().tolist())
course_options = [f"Machine Learning (OULAD {m})" for m in unique_modules]
# Add a generic fallback option if needed
if "Machine Learning (OULAD AAA)" not in course_options:
    course_options = ["Machine Learning (OULAD AAA)"] + course_options
selected_course_option = st.sidebar.selectbox("Select Course", course_options, label_visibility="collapsed")
if "(OULAD " in selected_course_option:
    selected_module = selected_course_option.split(" (OULAD ")[1].replace(")", "")
else:
    selected_module = "AAA"

# Filter datasets based on module
df_filtered_risk = df_risk[df_risk['code_module'] == selected_module].copy()
if df_filtered_risk.empty:
    df_filtered_risk = df_risk.copy()

# Student Selector
curated_student_list = generate_curated_student_list(df_filtered_risk)
if not curated_student_list:
    curated_student_list = ["demo_student_hash_placeholder"]

hash_to_friendly = {}
for idx, raw_hash in enumerate(curated_student_list):
    row_data = df_filtered_risk[df_filtered_risk['student_id_hash'] == raw_hash]
    if not row_data.empty:
        real_id = row_data.iloc[0]['id_student']
        hash_to_friendly[raw_hash] = f"👤 MSSV: {real_id} (#{(idx+1)})"
    else:
        hash_to_friendly[raw_hash] = f"👤 Student #{(idx+1)} ({raw_hash[:8]}...)"

st.sidebar.markdown('<div class="field-label">Tra Cứu Học Viên (Student Hash)</div>', unsafe_allow_html=True)
search_mode = st.sidebar.radio("Chế độ tìm kiếm", ["Chọn từ danh sách", "Nhập mã hash thủ công"], label_visibility="collapsed")

if search_mode == "Chọn từ danh sách":
    selected_student = st.sidebar.selectbox(
        "Chọn học viên",
        curated_student_list,
        format_func=lambda x: hash_to_friendly.get(x, x),
        label_visibility="collapsed"
    )
else:
    selected_student = st.sidebar.text_input(
        "Nhập mã hash",
        value="79d86f4d0c556c37c879fb9ba278f9996d5f1f50468d8e26e13a19ba6b09c219",
        placeholder="Nhập mã hash...",
        label_visibility="collapsed"
    )

# Initialize session state for mock interactions log
if 'interactions_log' not in st.session_state:
    st.session_state.interactions_log = []

if 'current_student' not in st.session_state or st.session_state.current_student != selected_student:
    st.session_state.current_student = selected_student
    user_row = df_user_emb[df_user_emb['student_id_hash'] == selected_student]
    if not user_row.empty:
        st.session_state.custom_u_emb = np.array(user_row.iloc[0]['user_embedding'])
    else:
        st.session_state.custom_u_emb = None

# Gateway status check for footer
gateway_status = "online"
try:
    resp = requests.get(f"{GATEWAY_URL}/health", timeout=1.0)
    if resp.status_code != 200:
        gateway_status = "offline"
except Exception:
    gateway_status = "offline"
    
status_color = "#10b981" if gateway_status == "online" else "#ef4444"
status_text = "Gateway Connected" if gateway_status == "online" else "Gateway Offline"

st.sidebar.markdown(
    f"""
    <div class="sidebar-footer">
        <span class="status-indicator online" style="background-color: {status_color};"></span> {status_text}
    </div>
    """,
    unsafe_allow_html=True
)

# ─── MAIN APPLICATION NAVIGATION (Tabs) ───
tab_cohort, tab_student, tab_playground = st.tabs([
    "📊 Global Cohort Analytics",
    "👤 Individual Student Inspection",
    "🧪 Adaptive LMS Simulation"
])

# ====================================================================
# TAB 1: GLOBAL COHORT ANALYTICS
# ====================================================================
with tab_cohort:
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h1 style="font-size: 2rem; margin-bottom: 0.5rem; color: #f8fafc;">📊 Global Cohort Analytics</h1>
            <p style="color: #94a3b8; font-size: 1rem; margin: 0;">Phân tích tổng quan hiệu năng và phân phối rủi ro của toàn bộ lớp học.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.1rem; margin-bottom: 1rem; color: #f8fafc;">Mô hình phân phối rủi ro bỏ học (LightGBM)</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Display actual risk density histogram
        risk_bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        risk_labels = ["0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
        df_hist = pd.cut(df_filtered_risk['dropout_probability'], bins=risk_bins, labels=risk_labels, include_lowest=True).value_counts().reset_index()
        df_hist.columns = ['Risk Range', 'Student Count']
        df_hist['Risk Range'] = pd.Categorical(df_hist['Risk Range'], categories=risk_labels, ordered=True)
        df_hist = df_hist.sort_values(by='Risk Range')
        st.bar_chart(df_hist.set_index('Risk Range')[['Student Count']], color="#3b82f6", use_container_width=True)

    with col2:
        st.markdown(
            """
            <div class="glass-card" style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.1rem; margin-bottom: 1rem; color: #f8fafc;">Bản đồ nhiệt thấu hiểu kỹ năng (BKT Heatmap)</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Display BKT Skill Heatmap grouped by student risk bands
        df_student_risk = df_filtered_risk[['student_id_hash', 'dropout_probability']].copy()
        def get_risk_band(prob):
            if prob <= 0.3: return "🟢 Safe (<=30%)"
            elif prob <= 0.7: return "🟡 Medium (30-70%)"
            else: return "🔴 High (>70%)"
        df_student_risk['risk_band'] = df_student_risk['dropout_probability'].apply(get_risk_band)
        
        df_module_bkt_all = df_bkt[df_bkt['skill_name'].str.startswith(selected_module)]
        
        if not df_module_bkt_all.empty:
            df_bkt_merged = df_module_bkt_all.merge(df_student_risk, left_on='user_id', right_on='student_id_hash', how='inner')
            if not df_bkt_merged.empty:
                df_pivot = df_bkt_merged.groupby(['risk_band', 'skill_name'])['correct_predictions'].mean().unstack().fillna(0.0) * 100
                df_pivot.index.name = "Cohort Risk Group"
                st.dataframe(df_pivot, use_container_width=True)
            else:
                st.info("No matching BKT mastery data found for this cohort.")
        else:
            st.info(f"No BKT mastery records found matching module {selected_module}.")

# ====================================================================
# TAB 2: INDIVIDUAL STUDENT INSPECTION
# ====================================================================
with tab_student:
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h1 style="font-size: 2rem; margin-bottom: 0.5rem; color: #f8fafc;">👤 Individual Student Inspection</h1>
            <p style="color: #94a3b8; font-size: 1rem; margin: 0;">Phân tích chi tiết hành vi và cập nhật mức độ hiểu bài trực tiếp của từng học viên.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Fetch student gateway profile
    live_data = fetch_student_profile_from_gateway(selected_student)
    
    # Local fallback
    student_risk_rows = df_risk[df_risk['student_id_hash'] == selected_student]
    if student_risk_rows.empty:
        fallback_risk = {"student_id_hash": selected_student, "dropout_probability": 0.0, "predicted_class": "Success", "id_student": "Unknown"}
    else:
        fallback_risk = student_risk_rows.iloc[0]
        
    if live_data:
        prob = live_data.get("dropout_probability", fallback_risk.get("dropout_probability", 0.0))
        pred_class = fallback_risk.get("predicted_class", "Success")
    else:
        prob = fallback_risk.get("dropout_probability", 0.0)
        pred_class = fallback_risk.get("predicted_class", "Success")
        
    # Badge element
    badge_class = "status-badge-risk" if prob > 0.5 else "status-badge-safe"
    badge_text = f"🔴 HIGH DROPOUT RISK ({prob*100:.2f}%)" if prob > 0.5 else f"🟢 SAFE ({prob*100:.2f}%)"
    
    st.markdown(
        f"""
        <div class="glass-card" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
            <div>
                <h3 style="margin: 0; color: #3b82f6 !important;">Student ID Profile Inspection</h3>
                <p style="margin: 0.2rem 0 0 0; color: #94a3b8;">Cloud ID Hash: <code>{selected_student}</code></p>
                <p style="margin: 0.2rem 0 0 0; color: #94a3b8;">Outcome Prediction: <strong>{pred_class}</strong></p>
            </div>
            <div>
                <span class="{badge_class}" style="font-size: 1.3rem; padding: 0.6rem 1.2rem;">{badge_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_inspect_left, col_inspect_right = st.columns(2)
    
    with col_inspect_left:
        st.markdown("##### 🧠 Chapter BKT Mastery Levels")
        with st.container(border=True):
            bkt_mastery_dict = {}
            if live_data and "bkt_mastery" in live_data:
                bkt_mastery_dict = live_data["bkt_mastery"]
            else:
                student_bkt_df = df_bkt[df_bkt['user_id'] == selected_student]
                for _, row in student_bkt_df.iterrows():
                    skill = row['skill_name']
                    for ch in ["C1", "C2", "C3", "C4", "C5", "C6"]:
                        if ch in skill:
                            bkt_mastery_dict[ch] = float(row['correct_predictions'])
            
            if bkt_mastery_dict:
                for ch, val in sorted(bkt_mastery_dict.items()):
                    st.write(f"**Chapter {ch} Mastery State:** {val*100:.1f}%")
                    st.progress(float(val))
            else:
                st.info("No chapter BKT mastery recorded yet for this student.")

    with col_inspect_right:
        st.markdown("##### 📈 Weekly Course Engagement Checkpoints")
        df_timeline = get_student_timeline_data(selected_student, prob)
        with st.container(border=True):
            chart_data = df_timeline.set_index("Mốc thời gian")[["Xác suất bỏ học (%)", "Độ thành thục BKT (%)"]]
            st.line_chart(chart_data, color=["#ef4444", "#10b981"], use_container_width=True)

    # Personalized Recommendations
    st.markdown("##### 🎯 Personalized Learning Materials Recommendations (LightGCN)")
    with st.container(border=True):
        top_5_items = None
        if live_data and "recommendations" in live_data:
            recs_df_data = []
            for item in live_data["recommendations"]:
                site_id = item["id_site"]
                act_type = get_vle_activity(site_id, df_lms)
                icon = get_activity_icon(act_type)
                recs_df_data.append({
                    "Material ID (VLE Site ID)": str(site_id),
                    "Content Type": f"{icon} {act_type}",
                    "Relevance Score": f"{item['score']:.4f}"
                })
            top_5_items = pd.DataFrame(recs_df_data)
        else:
            if st.session_state.custom_u_emb is not None:
                u_emb = st.session_state.custom_u_emb
                i_embs = np.stack(df_item_emb['item_embedding'].values)
                scores = np.dot(i_embs, u_emb)
                df_item_emb_scored = df_item_emb.copy()
                df_item_emb_scored['recommendation_score'] = scores
                top_5_raw = df_item_emb_scored.sort_values(by='recommendation_score', ascending=False).head(5)
                
                recs_df_data = []
                for idx, row in top_5_raw.iterrows():
                    site_id = row['id_site']
                    act_type = get_vle_activity(site_id, df_lms)
                    icon = get_activity_icon(act_type)
                    recs_df_data.append({
                        "Material ID (VLE Site ID)": str(site_id),
                        "Content Type": f"{icon} {act_type}",
                        "Relevance Score": f"{row['recommendation_score']:.4f}"
                    })
                top_5_items = pd.DataFrame(recs_df_data)
                
        if top_5_items is not None and not top_5_items.empty:
            st.dataframe(top_5_items, use_container_width=True)
        else:
            st.warning("No embedding vectors found to generate recommendations.")

# ====================================================================
# TAB 3: ADAPTIVE LMS SIMULATION
# ====================================================================
with tab_playground:
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h1 style="font-size: 2rem; margin-bottom: 0.5rem; color: #f8fafc;">🧪 Adaptive LMS Simulation</h1>
            <p style="color: #94a3b8; font-size: 1rem; margin: 0;">Môi trường giả lập hành vi click stream và nộp bài kiểm tra để cập nhật mô hình thời gian thực.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_play_left, col_play_right = st.columns([6, 6])
    
    with col_play_left:
        # Mock Click Event
        st.markdown("##### 📖 Mock Student Clickstream Interaction")
        with st.form("mock_click_form"):
            site_options = sorted(df_lms['id_site'].unique().astype(int).tolist())[:20]
            selected_site = st.selectbox("Select Learning Resource ID", site_options)
            activity_label = get_vle_activity(selected_site, df_lms)
            st.write(f"Resource type: **{activity_label}**")
            
            click_submit = st.form_submit_button("🚀 Submit Clickstream Event")
            if click_submit:
                t_now = datetime.now().strftime('%H:%M:%S')
                item_row = df_item_emb[df_item_emb['id_site'] == str(selected_site)]
                if not item_row.empty and st.session_state.custom_u_emb is not None:
                    i_emb = np.array(item_row.iloc[0]['item_embedding'])
                    new_vec = st.session_state.custom_u_emb + 0.3 * i_emb
                    st.session_state.custom_u_emb = new_vec / np.linalg.norm(new_vec)
                    
                success, details = send_kafka_event(selected_student, selected_site, activity_label)
                if success:
                    st.session_state.interactions_log.append(f"🟢 [{t_now}] Click tracked: site={selected_site} ({activity_label})")
                else:
                    st.session_state.interactions_log.append(f"⚠️ [{t_now}] Gateway Click Error: {details}")
                st.rerun()

        # Mock Assignment Submission
        st.markdown("##### 📝 Mock Assessment Grade Submission")
        with st.form("mock_grade_form"):
            assignment_options = ["TMA C1", "TMA C2", "TMA C3", "TMA C4", "TMA C5", "TMA C6"]
            selected_assignment = st.selectbox("Select Assignment ID", assignment_options)
            mock_score = st.slider("Mock Assignment Score (%)", 0, 100, 75)
            
            grade_submit = st.form_submit_button("📝 Submit Assignment Grade")
            if grade_submit:
                t_now = datetime.now().strftime('%H:%M:%S')
                clean_assignment_id = selected_assignment.split(" ")[1]
                success, details = send_assessment_submission(selected_student, clean_assignment_id, mock_score)
                if success:
                    st.session_state.interactions_log.append(f"🟢 [{t_now}] Score {mock_score}% recorded for assignment {clean_assignment_id}: {details}")
                else:
                    st.session_state.interactions_log.append(f"⚠️ [{t_now}] Gateway Grade Error: {details}")
                st.rerun()

        if st.button("🔄 Reset Simulator & Gateway Demo State"):
            t_now = datetime.now().strftime('%H:%M:%S')
            success, details = reset_gateway_demo_state()
            if success:
                st.session_state.interactions_log.append(f"🔄 [{t_now}] {details}")
                user_row = df_user_emb[df_user_emb['student_id_hash'] == selected_student]
                if not user_row.empty:
                    st.session_state.custom_u_emb = np.array(user_row.iloc[0]['user_embedding'])
            else:
                st.session_state.interactions_log.append(f"⚠️ [{t_now}] Reset Error: {details}")
            st.rerun()
            
    with col_play_right:
        st.markdown("##### 🖥️ Real-time NRT Pipeline Execution Log Console")
        if st.session_state.interactions_log:
            log_html = "<br>".join(st.session_state.interactions_log[::-1])
            st.markdown(
                f'<div class="console-log">{log_html}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="console-log" style="color: #ef4444;">[No events transmitted in this session yet]</div>',
                unsafe_allow_html=True
            )

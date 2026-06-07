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

# ─── PAGE CONFIGURATION ───
st.set_page_config(
    page_title="B-LEARN: EdTech Analytics & Personalization",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom styling rules from style.css
style_path = 'dashboard/style.css'
if not os.path.exists(style_path):
    style_path = '/app/dashboard/style.css'
if os.path.exists(style_path):
    with open(style_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ─── SERVING LAYER CONNECTION ───
storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
storage_key = os.getenv("AZURE_STORAGE_KEY")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "b-learn-super-secret-key-1015")

# ─── HELPER FUNCTIONS ───
def get_vle_activity(site_id, df_lms):
    """Looks up activity type for a given site ID in df_lms."""
    if df_lms is not None and not df_lms.empty:
        try:
            match = df_lms[df_lms['id_site'] == int(site_id)]
            if not match.empty:
                return str(match.iloc[0]['activity_type'])
        except Exception:
            pass
    return "oucontent"

def get_activity_icon(act_type):
    """Returns a corresponding emoji icon for the VLE activity type."""
    act_type_lower = str(act_type).lower()
    if "content" in act_type_lower:
        return "📄"
    elif "forum" in act_type_lower:
        return "💬"
    elif "quiz" in act_type_lower:
        return "📝"
    elif "url" in act_type_lower:
        return "🔗"
    elif "resource" in act_type_lower:
        return "📦"
    elif "subpage" in act_type_lower:
        return "📖"
    else:
        return "💻"

def get_risk_band(p):
    if p <= 0.3: return "Safe"
    elif p <= 0.7: return "Warning"
    else: return "Alert"

# ─── API CONNECTIVITY UTILITIES ───
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

# ─── SIDEBAR: NAVIGATION & SELECTION ───
st.sidebar.header("🎓 B-Learn `version 2`")

# Load datasets
with st.spinner("⏳ Loading dataset..."):
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
            df_feats = load_serving_data("risk_features.parquet")
        except Exception:
            df_feats = pd.DataFrame()
            
        try:
            df_lms = load_serving_data("lms_simulator.parquet")
        except Exception:
            df_lms = pd.DataFrame({
                "id_site": df_item_emb["id_site"].unique().astype(int),
                "activity_type": np.random.choice(["oucontent", "forumng", "url", "resource", "subpage", "quiz"], size=len(df_item_emb["id_site"].unique()))
            })
    except Exception as e:
        st.error(f"Error loading serving data: {e}")
        st.stop()

# Ensure standard columns are available
if 'id_student' not in df_risk.columns:
    import hashlib
    df_risk['id_student'] = df_risk['student_id_hash'].apply(lambda h: str(int(hashlib.md5(h.encode('utf-8')).hexdigest()[:6], 16) % 900000 + 100000))

# Merge risk predictions and features for detailed visualizations
if not df_feats.empty:
    df_risk_merged = pd.merge(df_risk, df_feats, on='student_id_hash', how='inner', suffixes=('', '_feat'))
else:
    df_risk_merged = df_risk.copy()
    np.random.seed(42)
    df_risk_merged['total_clicks'] = np.random.randint(20, 200, size=len(df_risk_merged))
    df_risk_merged['avg_score'] = np.random.uniform(50, 95, size=len(df_risk_merged))
    df_risk_merged['active_days'] = np.random.randint(5, 30, size=len(df_risk_merged))
    df_risk_merged['avg_daily_clicks'] = df_risk_merged['total_clicks'] / df_risk_merged['active_days']
    df_risk_merged['submission_count'] = np.random.randint(1, 10, size=len(df_risk_merged))
    df_risk_merged['late_submissions'] = np.random.randint(0, 3, size=len(df_risk_merged))
    df_risk_merged['studied_credits'] = np.random.choice([60, 120, 180], size=len(df_risk_merged))
    df_risk_merged['gender'] = np.random.choice(['M', 'F'], size=len(df_risk_merged))
    df_risk_merged['age_band'] = np.random.choice(['0-35', '35-55', '55+'], size=len(df_risk_merged))
    df_risk_merged['disability'] = np.random.choice(['N', 'Y'], size=len(df_risk_merged))
    df_risk_merged['imd_band'] = np.random.choice(['10-20%', '50-60%', '90-100%'], size=len(df_risk_merged))
    df_risk_merged['region'] = np.random.choice(['London Region', 'West Midlands', 'East Anglian'], size=len(df_risk_merged))
    df_risk_merged['engagement_span'] = df_risk_merged['total_clicks'] * 1.5
    df_risk_merged['engagement_momentum'] = df_risk_merged['avg_daily_clicks'] * 1.1

# View Mode toggle
view_mode = st.sidebar.radio(
    "Navigation Mode",
    ["👤 Single Student Inspection", "📊 Universal Analytics Statistics"]
)

bkt_options = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']

if view_mode == "👤 Single Student Inspection":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Student Context Filters")
    
    # Course Filter Parameter
    unique_modules = sorted(df_risk['code_module'].unique().tolist())
    course_options = [f"OULAD {m}" for m in unique_modules]
    selected_course_option = st.sidebar.selectbox("Select Course Module", course_options)
    selected_module = selected_course_option.split(" ")[1]
    
    # Filter datasets based on module selection
    df_filtered_risk = df_risk[df_risk['code_module'] == selected_module].copy()

    # Student Selector Parameter
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

    selected_student = st.sidebar.selectbox(
        "Select Student Hash",
        curated_student_list,
        format_func=lambda x: hash_to_friendly.get(x, x)
    )

    # Line Chart Parameter: Select BKT chapters to show
    plot_chapters = st.sidebar.multiselect('Select BKT Chapters', bkt_options, bkt_options[:3])

    # Timeline height parameter
    plot_height = st.sidebar.slider('Specify timeline height', 150, 400, 200)

else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Universal Filters")
    
    # Universal scope modules
    unique_modules = sorted(df_risk['code_module'].unique().tolist())
    course_options = ["All Modules"] + [f"OULAD {m}" for m in unique_modules]
    selected_course_option = st.sidebar.selectbox("Select Course Scope", course_options)
    
    # Line chart height parameter
    plot_height = st.sidebar.slider('Specify chart height', 150, 400, 250)

st.sidebar.markdown(
    """
    ---
    Created with ❤️ by **B-Learn Team**.
    """
)

# Gateway status check for footer
gateway_status = "online"
try:
    resp = requests.get(f"{GATEWAY_URL}/health", timeout=1.0)
    if resp.status_code != 200:
        gateway_status = "offline"
except Exception:
    gateway_status = "offline"
    
status_color = "#10B981" if gateway_status == "online" else "#EF4444"
status_text = "Gateway Connected" if gateway_status == "online" else "Gateway Offline"

st.sidebar.markdown(
    f"""
    <div class="sidebar-footer">
        <span class="status-indicator online" style="background-color: {status_color};"></span> {status_text}
    </div>
    """,
    unsafe_allow_html=True
)

# ====================================================================
# VIEW 1: SINGLE STUDENT INSPECTION
# ====================================================================
if view_mode == "👤 Single Student Inspection":
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
        bkt_mastery_dict = live_data.get("bkt_mastery", {})
    else:
        prob = fallback_risk.get("dropout_probability", 0.0)
        pred_class = fallback_risk.get("predicted_class", "Success")
        
        # Extract BKT masteries from dataframe
        bkt_mastery_dict = {}
        student_bkt_df = df_bkt[df_bkt['user_id'] == selected_student]
        for _, row in student_bkt_df.iterrows():
            skill = row['skill_name']
            for ch in bkt_options:
                if ch in skill:
                    bkt_mastery_dict[ch] = float(row['correct_predictions'])

    # Calculate student BKT averages
    bkt_avg = np.mean(list(bkt_mastery_dict.values())) * 100 if bkt_mastery_dict else 65.0
    cohort_risk_avg = df_filtered_risk['dropout_probability'].mean() * 100

    if 'interactions_log' not in st.session_state:
        st.session_state.interactions_log = []

    if 'current_student' not in st.session_state or st.session_state.current_student != selected_student:
        st.session_state.current_student = selected_student
        user_row = df_user_emb[df_user_emb['student_id_hash'] == selected_student]
        if not user_row.empty:
            st.session_state.custom_u_emb = np.array(user_row.iloc[0]['user_embedding'])
        else:
            st.session_state.custom_u_emb = None

    # Get student actual click and score metrics from merged data
    df_student_feats = df_risk_merged[df_risk_merged['student_id_hash'] == selected_student]
    if not df_student_feats.empty:
        student_clicks = float(df_student_feats.iloc[0].get('total_clicks', 45.0))
        student_score = float(df_student_feats.iloc[0].get('avg_score', 75.0))
        active_days = int(df_student_feats.iloc[0].get('active_days', 10))
        submission_count = int(df_student_feats.iloc[0].get('submission_count', 3))
        late_submissions = int(df_student_feats.iloc[0].get('late_submissions', 0))
        studied_credits = int(df_student_feats.iloc[0].get('studied_credits', 60))
    else:
        student_clicks = 45.0
        student_score = 75.0
        active_days = 10
        submission_count = 3
        late_submissions = 0
        studied_credits = 60

    # Add simulated clickstream interactions locally
    student_clicks += st.session_state.get('simulated_clicks', 0)
    
    # Add simulated assessment scores locally
    sim_scores = st.session_state.get('simulated_scores', [])
    if sim_scores:
        student_score = (student_score * 3 + sum(sim_scores)) / (3 + len(sim_scores))

    # Calculate cohort averages
    df_cohort_module = df_risk_merged[df_risk_merged['code_module'] == selected_module]
    if not df_cohort_module.empty:
        cohort_clicks_avg = df_cohort_module['total_clicks'].mean()
        cohort_score_avg = df_cohort_module['avg_score'].mean()
        cohort_active_avg = df_cohort_module['active_days'].mean()
        cohort_sub_avg = df_cohort_module['submission_count'].mean()
        cohort_late_avg = df_cohort_module['late_submissions'].mean()
        cohort_credits_avg = df_cohort_module['studied_credits'].mean()
    else:
        cohort_clicks_avg = 52.0
        cohort_score_avg = 72.8
        cohort_active_avg = 12.5
        cohort_sub_avg = 4.2
        cohort_late_avg = 0.5
        cohort_credits_avg = 90.0

    # ─── ROW A: DENSE ACADEMIC PERFORMANCE METRICS ───
    st.markdown('### 📊 Student Academic Diagnostics')
    col1, col2, col3, col4 = st.columns(4)

    # 1. Dropout Risk Metric Card
    risk_pct = f"{prob * 100:.2f}%"
    risk_band = get_risk_band(prob)
    risk_delta = f"{((prob * 100) - cohort_risk_avg):+.1f}% vs Cohort"
    col1.metric("Dropout Risk Probability", risk_pct, risk_delta, delta_color="inverse")

    # 2. Avg Assignment Grade
    score_pct = f"{student_score:.1f}%"
    score_delta = f"{(student_score - cohort_score_avg):+.1f}% vs Cohort"
    col2.metric("Avg Assignment Grade", score_pct, score_delta)

    # 3. Chapter BKT Mastery
    mastery_str = f"{bkt_avg:.1f}%"
    cohort_bkt_avg = 68.4
    bkt_delta = f"{(bkt_avg - cohort_bkt_avg):+.1f}% vs Average"
    col3.metric("BKT Avg Skill Mastery", mastery_str, bkt_delta)

    # 4. Total studied credits
    credits_str = f"{studied_credits} credits"
    credits_delta = f"{(studied_credits - cohort_credits_avg):+.0f} vs Cohort"
    col4.metric("Academic Load (Credits)", credits_str, credits_delta)

    # ─── ROW B: DENSE BEHAVIORAL ENGAGEMENT METRICS ───
    st.markdown('### ⚡ Student Engagement & LMS Load')
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)

    # 1. Total click count
    clicks_str = f"{int(student_clicks)} clicks"
    clicks_delta = f"{(student_clicks - cohort_clicks_avg):+.0f} vs Cohort"
    col_b1.metric("Total LMS Clicks", clicks_str, clicks_delta)

    # 2. Active days count
    days_str = f"{active_days} days"
    days_delta = f"{(active_days - cohort_active_avg):+.1f} vs Cohort"
    col_b2.metric("LMS Active Days", days_str, days_delta)

    # 3. Submissions count
    subs_str = f"{submission_count} submissions"
    subs_delta = f"{(submission_count - cohort_sub_avg):+.1f} vs Cohort"
    col_b3.metric("Assignments Submitted", subs_str, subs_delta)

    # 4. Late submissions count
    late_str = f"{late_submissions} late"
    late_delta = f"{(late_submissions - cohort_late_avg):+.1f} vs Cohort"
    col_b4.metric("Late Submissions", late_str, late_delta, delta_color="inverse")

    # ─── ROW C: TIMELINE & SKILL BARS ───
    st.markdown('### 📈 Student Diagnostics curves & Skill Profile')
    col_c1, col_c2 = st.columns((7, 5))
    
    with col_c1:
        st.markdown("##### Cumulative Checkpoint Timelines (Dropout Risk vs BKT)")
        df_timeline = get_student_timeline_data(selected_student, prob)
        chart_data = df_timeline.set_index("Mốc thời gian")[["Xác suất bỏ học (%)", "Độ thành thục BKT (%)"]]
        # Native line chart provides high performance and aligns perfectly with styling
        st.line_chart(chart_data, height=plot_height)
        
    with col_c2:
        st.markdown("##### BKT Chapter Mastery Profile (Chapters C1 - C6)")
        if bkt_mastery_dict:
            df_bkt_profile = pd.DataFrame({
                "Chương": [f"Chương {ch}" for ch in bkt_mastery_dict.keys()],
                "Độ thành thục (%)": [v * 100 for v in bkt_mastery_dict.values()]
            }).set_index("Chương")
            st.bar_chart(df_bkt_profile, height=plot_height)
        else:
            st.info("Không có dữ liệu BKT cho học viên này.")

    # ─── ROW D: PEER COMPARISON & SITE INTERACTIONS ───
    st.markdown('### 👥 Engagement Comparison & Learning Breakdown')
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.markdown("##### Total Clicks comparison (Selected Student vs Cohort)")
        df_clicks_comp = pd.DataFrame({
            "Đối tượng": ["Học viên", "Trung bình khóa"],
            "Lượt clicks": [student_clicks, cohort_clicks_avg]
        }).set_index("Đối tượng")
        st.bar_chart(df_clicks_comp, height=180)

    with col_d2:
        st.markdown("##### LMS Site Content Click Breakdown")
        vle_counts = {"Video": 15, "PDF": 10, "Quiz": 8, "Forum": 18, "Resource": 6}
        vle_counts["Quiz"] += len(sim_scores)
        vle_counts["Video"] += st.session_state.get('simulated_clicks', 0)
        df_vle = pd.DataFrame({
            "Hoạt động": list(vle_counts.keys()),
            "Lượt tương tác": list(vle_counts.values())
        }).set_index("Hoạt động")
        st.bar_chart(df_vle, height=180)

    # ─── ROW E: ADAPTIVE PLAYGROUND & RECOMMENDATIONS ───
    st.markdown('### 🎯 Sandbox & Personalized Recommendations')
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown('##### Personalized Learning Materials (LightGCN recommendations)')
        top_5_items = None
        if live_data and "recommendations" in live_data:
            recs_df_data = []
            for item in live_data["recommendations"]:
                site_id = item["id_site"]
                act_type = get_vle_activity(site_id, df_lms)
                icon = get_activity_icon(act_type)
                recs_df_data.append({
                    "VLE Site ID": str(site_id),
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
                        "VLE Site ID": str(site_id),
                        "Content Type": f"{icon} {act_type}",
                        "Relevance Score": f"{row['recommendation_score']:.4f}"
                    })
                top_5_items = pd.DataFrame(recs_df_data)
                
        if top_5_items is not None and not top_5_items.empty:
            st.dataframe(top_5_items, use_container_width=True)
        else:
            st.warning("No embedding vectors found to generate recommendations.")

    with col_e2:
        st.markdown('##### 🎮 LMS Simulator Sandbox')
        with st.container(border=True):
            sim_col1, sim_col2 = st.columns(2)
            with sim_col1:
                site_options = sorted(df_lms['id_site'].unique().astype(int).tolist())[:10]
                selected_site = st.selectbox("Mock Site ID", site_options)
                activity_label = get_vle_activity(selected_site, df_lms)
                
                if st.button("🚀 Send Clickstream"):
                    t_now = datetime.now().strftime('%H:%M:%S')
                    item_row = df_item_emb[df_item_emb['id_site'] == str(selected_site)]
                    if not item_row.empty and st.session_state.custom_u_emb is not None:
                        i_emb = np.array(item_row.iloc[0]['item_embedding'])
                        new_vec = st.session_state.custom_u_emb + 0.3 * i_emb
                        st.session_state.custom_u_emb = new_vec / np.linalg.norm(new_vec)
                        
                    success, details = send_kafka_event(selected_student, selected_site, activity_label)
                    if success:
                        st.session_state.interactions_log.append(f"🟢 [{t_now}] Click: site={selected_site} ({activity_label})")
                        if 'simulated_clicks' not in st.session_state:
                            st.session_state.simulated_clicks = 0
                        st.session_state.simulated_clicks += 1
                    else:
                        st.session_state.interactions_log.append(f"⚠️ [{t_now}] Gateway Error: {details}")
                    st.rerun()
                    
            with sim_col2:
                assignment_options = ["TMA C1", "TMA C2", "TMA C3", "TMA C4", "TMA C5", "TMA C6"]
                selected_assignment = st.selectbox("Assignment Chapter", assignment_options)
                mock_score = st.slider("Score (%)", 0, 100, 80)
                
                if st.button("📝 Submit Grade"):
                    t_now = datetime.now().strftime('%H:%M:%S')
                    clean_assignment_id = selected_assignment.split(" ")[1]
                    success, details = send_assessment_submission(selected_student, clean_assignment_id, mock_score)
                    if success:
                        st.session_state.interactions_log.append(f"🟢 [{t_now}] Grade {mock_score}% on {clean_assignment_id}: {details}")
                        if 'simulated_scores' not in st.session_state:
                            st.session_state.simulated_scores = []
                        st.session_state.simulated_scores.append(mock_score)
                    else:
                        st.session_state.interactions_log.append(f"⚠️ [{t_now}] Gateway Error: {details}")
                    st.rerun()
 
            col_reset, col_space = st.columns((5, 7))
            with col_reset:
                if st.button("🔄 Reset State", use_container_width=True):
                    t_now = datetime.now().strftime('%H:%M:%S')
                    success, details = reset_gateway_demo_state()
                    if success:
                        st.session_state.interactions_log.append(f"🔄 [{t_now}] {details}")
                        if 'simulated_clicks' in st.session_state:
                            del st.session_state.simulated_clicks
                        if 'simulated_scores' in st.session_state:
                            del st.session_state.simulated_scores
                        user_row = df_user_emb[df_user_emb['student_id_hash'] == selected_student]
                        if not user_row.empty:
                            st.session_state.custom_u_emb = np.array(user_row.iloc[0]['user_embedding'])
                    else:
                        st.session_state.interactions_log.append(f"⚠️ [{t_now}] Reset Error: {details}")
                    st.rerun()

            # Console logs
            if st.session_state.interactions_log:
                log_html = "<br>".join(st.session_state.interactions_log[::-1])
                st.markdown(f'<div class="console-log">{log_html}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="console-log" style="color: #ef4444;">[No events logged]</div>', unsafe_allow_html=True)

# ====================================================================
# VIEW 2: UNIVERSAL ANALYTICS STATISTICS
# ====================================================================
else:
    # Filter datasets based on module scope selection
    if selected_course_option == "All Modules":
        df_univ_risk_merged = df_risk_merged
        df_univ_bkt = df_bkt
        scope_title = "All OULAD Modules"
    else:
        mod = selected_course_option.split(" ")[1]
        df_univ_risk_merged = df_risk_merged[df_risk_merged['code_module'] == mod]
        df_univ_bkt = df_bkt[df_bkt['skill_name'].str.startswith(mod)]
        scope_title = f"Module {mod}"

    # Calculate global cohort stats
    total_enrolled = len(df_univ_risk_merged)
    avg_univ_risk = df_univ_risk_merged['dropout_probability'].mean() * 100 if total_enrolled > 0 else 0.0
    avg_univ_score = df_univ_risk_merged['avg_score'].mean() if total_enrolled > 0 else 0.0
    avg_univ_clicks = df_univ_risk_merged['total_clicks'].mean() if total_enrolled > 0 else 0.0
    avg_univ_active_days = df_univ_risk_merged['active_days'].mean() if total_enrolled > 0 else 0.0
    avg_univ_submissions = df_univ_risk_merged['submission_count'].mean() if total_enrolled > 0 else 0.0
    avg_univ_late = df_univ_risk_merged['late_submissions'].mean() if total_enrolled > 0 else 0.0
    avg_univ_late_rate = (avg_univ_late / avg_univ_submissions * 100) if avg_univ_submissions > 0 else 0.0
    avg_univ_credits = df_univ_risk_merged['studied_credits'].mean() if total_enrolled > 0 else 0.0
    avg_univ_mastery = df_univ_bkt['correct_predictions'].astype(float).mean() * 100 if not df_univ_bkt.empty else 67.8

    # ─── ROW A: DENSE ACADEMIC KPIs ───
    st.markdown(f'### 📊 Universal Academic KPIs — {scope_title}')
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    
    col_u1.metric("Total Cohort Size", f"{total_enrolled:,} Students")
    col_u2.metric("Cohort Avg Dropout Risk", f"{avg_univ_risk:.2f}%")
    col_u3.metric("Cohort Avg Grade Score", f"{avg_univ_score:.1f}%")
    col_u4.metric("Avg BKT Skill Mastery", f"{avg_univ_mastery:.1f}%")

    # ─── ROW B: DENSE BEHAVIORAL KPIs ───
    st.markdown('### ⚡ Universal Engagement & LMS Load')
    col_ub1, col_ub2, col_ub3, col_ub4 = st.columns(4)

    total_clicks_sum = df_univ_risk_merged['total_clicks'].sum() if total_enrolled > 0 else 0
    col_ub1.metric("Total LMS Clicks Volume", f"{int(total_clicks_sum):,} clicks")
    col_ub2.metric("Avg LMS Active Days", f"{avg_univ_active_days:.1f} days")
    col_ub3.metric("Avg Submissions", f"{avg_univ_submissions:.1f}")
    col_ub4.metric("Late Submission Rate", f"{avg_univ_late_rate:.1f}%", delta_color="inverse")

    # ─── ROW C: LONGITUDINAL TRENDS & MODULE RISK ───
    st.markdown('### 📈 Cohort Trends & Module Comparison')
    col_uc1, col_uc2 = st.columns((7, 5))

    with col_uc1:
        st.markdown("##### Cohort Average Longitudinal Timeline (Risk vs BKT)")
        df_cohort_timeline = get_student_timeline_data("cohort_average_seed", avg_univ_risk / 100.0)
        chart_data_univ = df_cohort_timeline.set_index("Mốc thời gian")[["Xác suất bỏ học (%)", "Độ thành thục BKT (%)"]]
        st.line_chart(chart_data_univ, height=plot_height)

    with col_uc2:
        st.markdown("##### Average Dropout Risk by Course Module (%)")
        df_mod_risk = df_risk_merged.groupby('code_module')['dropout_probability'].mean().reset_index()
        df_mod_risk['dropout_probability'] = df_mod_risk['dropout_probability'] * 100
        df_mod_risk.columns = ["Module", "Avg Risk (%)"]
        st.bar_chart(df_mod_risk.set_index("Module"), color="#F59E0B", height=plot_height)

    # ─── ROW D: DEMOGRAPHICS AND RISKS ───
    st.markdown('### 👥 Demographic Risk profiles & BKT Masteries')
    col_ud1, col_ud2 = st.columns(2)

    with col_ud1:
        st.markdown('##### Average Dropout Risk by Demographic Attribute')
        demo_attr = st.selectbox(
            "Select Demographic Attribute for Breakdown",
            ["highest_education", "gender", "age_band", "disability", "imd_band", "region"],
            index=0,
            key="univ_demo_selectbox"
        )
        df_grouped = df_univ_risk_merged.groupby(demo_attr)['dropout_probability'].mean().reset_index()
        df_grouped['dropout_probability'] = df_grouped['dropout_probability'] * 100
        df_grouped.columns = [demo_attr.replace('_', ' ').title(), 'Avg Dropout Risk (%)']
        st.bar_chart(df_grouped.set_index(df_grouped.columns[0]), color="#EF4444", height=200)

    with col_ud2:
        st.markdown('##### Average BKT Mastery by Dropout Risk Band')
        # Map risk values to bands
        df_student_risk = df_univ_risk_merged[['student_id_hash', 'dropout_probability']].copy()
        df_student_risk['risk_band'] = df_student_risk['dropout_probability'].apply(get_risk_band)
        df_bkt_merged = df_bkt.merge(df_student_risk, left_on='user_id', right_on='student_id_hash', how='inner')
        if not df_bkt_merged.empty:
            df_bkt_risk = df_bkt_merged.groupby('risk_band')['correct_predictions'].mean().reset_index()
            df_bkt_risk['correct_predictions'] = df_bkt_risk['correct_predictions'] * 100
            df_bkt_risk.columns = ["Risk Band", "Avg Mastery (%)"]
            st.bar_chart(df_bkt_risk.set_index("Risk Band"), color="#10B981", height=200)
        else:
            st.info("Không tìm thấy dữ liệu BKT tương thích.")

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

# Load custom styling rules from style.css (copied pattern from example)
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

# ─── SIDEBAR: PARAMETERS (Pattern matching example) ───
st.sidebar.header("🎓 B-Learn `version 2`")

# Load data with local caching
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
bkt_options = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
plot_chapters = st.sidebar.multiselect('Select BKT Chapters', bkt_options, bkt_options[:3])

# Timeline height parameter
plot_height = st.sidebar.slider('Specify timeline height', 150, 400, 200)

st.sidebar.markdown(
    """
    ---
    Created with ❤️ by **B-Learn Team**.
    """
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

# Calculate selected student avg BKT mastery
bkt_avg = np.mean(list(bkt_mastery_dict.values())) * 100 if bkt_mastery_dict else 65.0
cohort_risk_avg = df_filtered_risk['dropout_probability'].mean() * 100

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


# ====================================================================
# ROW A: KEY PERFORMANCE METRICS
# ====================================================================
st.markdown('### Learning Key Metrics')
col1, col2, col3 = st.columns(3)

# Selected Student Risk
risk_pct = f"{prob * 100:.2f}%"
risk_label = "Student Dropout Risk"
col1.metric(risk_label, risk_pct, f"Class: {pred_class}")

# Cohort Avg Risk
col2.metric("Cohort Average Risk", f"{cohort_risk_avg:.2f}%", f"Total: {len(df_filtered_risk)} Students")

# Student BKT Avg Mastery
col3.metric("Student BKT Avg Mastery", f"{bkt_avg:.1f}%", f"Active Chapters: {len(bkt_mastery_dict)}")


# ====================================================================
# ROW B: HEATMAP & DISTRIBUTION PLOT
# ====================================================================
c1, c2 = st.columns((7, 3))

with c1:
    st.markdown('### BKT skill mastery Heatmap across Cohort Risk Groups')
    df_student_risk = df_filtered_risk[['student_id_hash', 'dropout_probability']].copy()
    def get_risk_band(p):
        if p <= 0.3: return "🟢 Safe"
        elif p <= 0.7: return "🟡 Medium"
        else: return "🔴 High"
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

with c2:
    st.markdown('### Dropout Risk Distribution')
    # Build clean risk distribution
    risk_bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    risk_labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    df_hist = pd.cut(df_filtered_risk['dropout_probability'], bins=risk_bins, labels=risk_labels, include_lowest=True).value_counts().reset_index()
    df_hist.columns = ['Risk Range', 'Student Count']
    df_hist['Risk Range'] = pd.Categorical(df_hist['Risk Range'], categories=risk_labels, ordered=True)
    df_hist = df_hist.sort_values(by='Risk Range')
    st.bar_chart(df_hist.set_index('Risk Range')[['Student Count']], color="#3b82f6", use_container_width=True)


# ====================================================================
# ROW C: CHECKPOINT TIMELINE LINE CHART
# ====================================================================
st.markdown('### Longitudinal Checkpoint Timelines')
df_timeline = get_student_timeline_data(selected_student, prob)

# Filter timeline BKT columns according to selected chapters parameter in sidebar
timeline_cols = ["Xác suất bỏ học (%)"]
for ch in plot_chapters:
    timeline_cols.append("Độ thành thục BKT (%)")  # Simple mapping

chart_data = df_timeline.set_index("Mốc thời gian")[["Xác suất bỏ học (%)", "Độ thành thục BKT (%)"]]
st.line_chart(chart_data, color=["#ef4444", "#10b981"], height=plot_height, use_container_width=True)


# ====================================================================
# ROW D: RECOMMENDATIONS & INTERACTIVE LMS SIMULATOR
# ====================================================================
col_d1, col_d2 = st.columns((6, 6))

with col_d1:
    st.markdown('### Personalized Content Recommendations (LightGCN)')
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

with col_d2:
    st.markdown('### Adaptive LMS Simulator & Real-time loops')
    with st.container(border=True):
        st.caption("Submit clickstream or scores to trigger direct Bayesian BKT updates and LightGBM models.")
        
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
                else:
                    st.session_state.interactions_log.append(f"⚠️ [{t_now}] Gateway Error: {details}")
                st.rerun()

        col_reset, col_space = st.columns((4, 8))
        with col_reset:
            if st.button("🔄 Reset Demo State", use_container_width=True):
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

        # Console logs
        if st.session_state.interactions_log:
            log_html = "<br>".join(st.session_state.interactions_log[::-1])
            st.markdown(f'<div class="console-log">{log_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="console-log" style="color: #ef4444;">[No events logged]</div>', unsafe_allow_html=True)

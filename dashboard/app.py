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
import plotly.express as px
import plotly.graph_objects as go

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

# ─── PLOTLY GRAPH RENDERING FUNCTIONS ───
def render_cohort_heatmap(df_pivot, key_suffix=""):
    """Renders a high-contrast interactive heatmap for cohort skill masteries using go.Heatmap."""
    z_data = df_pivot.values
    x_labels = df_pivot.columns.tolist()
    
    # Strip emojis from index labels to prevent browser text layout crashes
    y_labels = []
    for val in df_pivot.index.tolist():
        s = str(val)
        for emoji in ["🟢", "🟡", "🔴", "🟢 ", "🟡 ", "🔴 "]:
            s = s.replace(emoji, "")
        y_labels.append(s.strip())
        
    # Scale values to percentage (0 - 100) for display
    z_display = z_data * 100
    
    fig = go.Figure(data=go.Heatmap(
        z=z_display,
        x=x_labels,
        y=y_labels,
        colorscale=[[0.0, "#EF4444"], [0.5, "#F59E0B"], [1.0, "#10B981"]],
        zmin=0.0,
        zmax=100.0,
        text=z_display,
        texttemplate="%{text:.1f}%",
        textfont={"size": 11, "family": "Outfit", "color": "#0F172A"},
        showscale=True,
        colorbar=dict(
            title=dict(
                text="Mastery %",
                side="top",
                font=dict(color="#64748B")
            ),
            tickfont=dict(color="#64748B")
        )
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        xaxis=dict(tickfont=dict(color="#64748B")),
        yaxis=dict(tickfont=dict(color="#64748B")),
        margin=dict(l=20, r=20, t=10, b=20),
        height=280
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"cohort_mastery_heatmap_{key_suffix}")

def render_student_radar(bkt_mastery_dict, key_suffix=""):
    """Generates an elegant Radar chart mapping current student chapter masteries."""
    categories = sorted(list(bkt_mastery_dict.keys()))
    values = [float(bkt_mastery_dict[cat]) for cat in categories]
    
    if not categories:
        st.info("No mastery tracks initialized for mapping.")
        return

    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[v * 100 for v in values_closed],
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(59, 130, 246, 0.15)",
        line=dict(color="#3B82F6", width=3),
        name="Student Mastery Profile"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#64748B"),
                gridcolor="rgba(0, 0, 0, 0.08)"
            ),
            angularaxis=dict(
                tickfont=dict(color="#0F172A", size=11),
                gridcolor="rgba(0, 0, 0, 0.08)"
            ),
            bgcolor="rgba(241, 245, 249, 0.4)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=25, b=25),
        height=280,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"student_radar_chart_{key_suffix}")

def render_engagement_comparison(student_clicks, cohort_avg_clicks, key_suffix=""):
    """Compare selected student clicks against peer average using a gauge indicator."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = student_clicks,
        domain = {'x': [0, 1], 'y': [0, 1]},
        delta = {'reference': cohort_avg_clicks, 'increasing': {'color': '#10B981'}, 'decreasing': {'color': '#EF4444'}},
        gauge = {
            'axis': {'range': [0, max(float(student_clicks), float(cohort_avg_clicks), 10.0) * 1.4], 'tickwidth': 1, 'tickcolor': "#64748B"},
            'bar': {'color': "#3B82F6"},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, cohort_avg_clicks * 0.7], 'color': 'rgba(239, 68, 68, 0.08)'},
                {'range': [cohort_avg_clicks * 0.7, cohort_avg_clicks * 1.2], 'color': 'rgba(245, 158, 11, 0.08)'},
                {'range': [cohort_avg_clicks * 1.2, max(float(student_clicks), float(cohort_avg_clicks), 10.0) * 1.4], 'color': 'rgba(16, 185, 129, 0.08)'}
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=40, b=20),
        height=180
    )
    st.plotly_chart(fig, use_container_width=True, key=f"student_engagement_gauge_{key_suffix}")

def render_module_risk_violin(df_risk, key_suffix=""):
    """Displays a box plot showing the risk distribution across modules."""
    fig = px.box(
        df_risk,
        x="code_module",
        y="dropout_probability",
        color="code_module",
        points="all",
        labels=dict(code_module="Course Module", dropout_probability="Dropout Risk Score"),
        color_discrete_sequence=["#3B82F6", "#60A5FA", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444"]
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, key=f"universal_violin_risk_{key_suffix}")

def render_student_cohort_scatter(student_hash, df_risk_merged, student_clicks, student_score, key_suffix=""):
    """Plots Average Assignment Score vs Total Clicks for the cohort, highlighting the selected student."""
    df_bg = df_risk_merged[df_risk_merged['student_id_hash'] != student_hash]
    
    fig = go.Figure()
    
    # Cohort background scatter
    fig.add_trace(go.Scatter(
        x=df_bg['total_clicks'],
        y=df_bg['avg_score'],
        mode='markers',
        marker=dict(
            size=6,
            color=df_bg['dropout_probability'] * 100,
            colorscale=[[0, '#10B981'], [0.5, '#F59E0B'], [1, '#EF4444']],
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Risk %",
                    font=dict(color="#64748B")
                ),
                tickfont=dict(color="#64748B")
            ),
            opacity=0.6
        ),
        name="Cohort Peers",
        hovertemplate="Peer Student<br>Clicks: %{x}<br>Avg Score: %{y:.1f}%<br>Risk: %{marker.color:.1f}%<extra></extra>"
    ))
    
    # Current student highlight
    fig.add_trace(go.Scatter(
        x=[student_clicks],
        y=[student_score],
        mode='markers',
        marker=dict(
            size=14,
            color='#8B5CF6', # Premium Purple/Amethyst for contrast
            symbol='star',
            line=dict(color='#0F172A', width=2)
        ),
        name="Selected Student",
        hovertemplate="<b>Selected Student</b><br>Clicks: %{x}<br>Avg Score: %{y:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        xaxis=dict(
            title="Total Clicks",
            gridcolor="rgba(0, 0, 0, 0.05)",
            tickfont=dict(color="#64748B")
        ),
        yaxis=dict(
            title="Average Score (%)",
            gridcolor="rgba(0, 0, 0, 0.05)",
            tickfont=dict(color="#64748B"),
            range=[0, 105]
        ),
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True, key=f"student_cohort_scatter_{key_suffix}")

def render_student_timeline_plotly(df_timeline, key_suffix=""):
    """Displays an elegant, double-axis interactive line chart for risk & BKT mastery."""
    fig = go.Figure()
    
    # Dropout risk
    fig.add_trace(go.Scatter(
        x=df_timeline["Mốc thời gian"],
        y=df_timeline["Xác suất bỏ học (%)"],
        mode='lines+markers',
        name="Student Risk (%)",
        line=dict(color="#EF4444", width=3),
        marker=dict(size=8),
        yaxis="y1"
    ))
    
    # Risk baseline
    fig.add_trace(go.Scatter(
        x=df_timeline["Mốc thời gian"],
        y=df_timeline["Trường học (Risk Baseline) (%)"],
        mode='lines',
        name="Risk Baseline (%)",
        line=dict(color="#EF4444", width=1.5, dash='dash'),
        yaxis="y1"
    ))
    
    # BKT mastery
    fig.add_trace(go.Scatter(
        x=df_timeline["Mốc thời gian"],
        y=df_timeline["Độ thành thục BKT (%)"],
        mode='lines+markers',
        name="BKT Mastery (%)",
        line=dict(color="#10B981", width=3),
        marker=dict(size=8),
        yaxis="y2"
    ))
    
    # BKT baseline
    fig.add_trace(go.Scatter(
        x=df_timeline["Mốc thời gian"],
        y=df_timeline["Trường học (BKT Baseline) (%)"],
        mode='lines',
        name="BKT Baseline (%)",
        line=dict(color="#10B981", width=1.5, dash='dash'),
        yaxis="y2"
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        xaxis=dict(
            gridcolor="rgba(0, 0, 0, 0.05)",
            tickfont=dict(color="#64748B")
        ),
        yaxis=dict(
            title=dict(
                text="Dropout Risk (%)",
                font=dict(color="#EF4444")
            ),
            tickfont=dict(color="#EF4444"),
            gridcolor="rgba(0, 0, 0, 0.05)",
            range=[0, 105]
        ),
        yaxis2=dict(
            title=dict(
                text="BKT Mastery (%)",
                font=dict(color="#10B981")
            ),
            tickfont=dict(color="#10B981"),
            overlaying="y",
            side="right",
            range=[0, 105]
        ),
        margin=dict(l=40, r=40, t=10, b=30),
        height=280,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    st.plotly_chart(fig, use_container_width=True, key=f"timeline_plotly_{key_suffix}")

def render_universal_scatter(df_risk_merged, key_suffix=""):
    """Plots Average Assignment Score vs Total Clicks for all students, colored by predicted risk."""
    fig = px.scatter(
        df_risk_merged,
        x='total_clicks',
        y='avg_score',
        color='dropout_probability',
        color_continuous_scale=[[0, '#10B981'], [0.5, '#F59E0B'], [1, '#EF4444']],
        labels=dict(total_clicks="Total Clicks", avg_score="Average Score (%)", dropout_probability="Dropout Risk"),
        hover_data=['id_student', 'predicted_class', 'highest_education']
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        xaxis=dict(gridcolor="rgba(0, 0, 0, 0.05)", title="Total Clicks"),
        yaxis=dict(gridcolor="rgba(0, 0, 0, 0.05)", range=[0, 105], title="Average Score (%)"),
        margin=dict(l=40, r=20, t=10, b=40),
        height=280
    )
    st.plotly_chart(fig, use_container_width=True, key=f"universal_risk_scatter_{key_suffix}")

def render_demographic_risk_bars(df_risk_merged, demographic_col, key_suffix=""):
    """Displays average dropout probability across different categories of a demographic variable."""
    df_grouped = df_risk_merged.groupby(demographic_col)['dropout_probability'].mean().reset_index()
    df_grouped['dropout_probability'] = df_grouped['dropout_probability'] * 100
    df_grouped = df_grouped.sort_values(by='dropout_probability', ascending=True)
    
    fig = px.bar(
        df_grouped,
        y=demographic_col,
        x='dropout_probability',
        orientation='h',
        labels={demographic_col: demographic_col.replace('_', ' ').title(), 'dropout_probability': 'Avg Dropout Risk (%)'},
        color='dropout_probability',
        color_continuous_scale=[[0, '#10B981'], [0.5, '#F59E0B'], [1, '#EF4444']],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        xaxis=dict(gridcolor="rgba(0, 0, 0, 0.05)", range=[0, 100], title="Avg Dropout Risk (%)"),
        yaxis=dict(gridcolor="rgba(0, 0, 0, 0.05)", title=""),
        coloraxis_showscale=False,
        margin=dict(l=40, r=20, t=10, b=40),
        height=280
    )
    st.plotly_chart(fig, use_container_width=True, key=f"demographic_risk_bars_{demographic_col}_{key_suffix}")

def render_feature_correlation_heatmap(df_risk_merged, key_suffix=""):
    """Plots correlation matrix of key numeric features and predicted dropout probability."""
    features = [
        'dropout_probability', 'total_clicks', 'active_days', 
        'avg_daily_clicks', 'engagement_span', 'engagement_momentum', 
        'avg_score', 'submission_count', 'late_submissions', 'studied_credits'
    ]
    valid_features = [f for f in features if f in df_risk_merged.columns]
    df_corr = df_risk_merged[valid_features].corr()
    
    label_map = {
        'dropout_probability': 'Dropout Risk',
        'total_clicks': 'Total Clicks',
        'active_days': 'Active Days',
        'avg_daily_clicks': 'Avg Daily Clicks',
        'engagement_span': 'Engagement Span',
        'engagement_momentum': 'Eng. Momentum',
        'avg_score': 'Avg Score',
        'submission_count': 'Submissions',
        'late_submissions': 'Late Subs',
        'studied_credits': 'Credits'
    }
    x_labels = [label_map.get(f, f) for f in valid_features]
    
    fig = px.imshow(
        df_corr.values,
        x=x_labels,
        y=x_labels,
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        text_auto=".2f"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0F172A", family="Outfit"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=320
    )
    st.plotly_chart(fig, use_container_width=True, key=f"feature_correlation_heatmap_{key_suffix}")

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

# Helper function for risk bands
def get_risk_band(p):
    if p <= 0.3: return "🟢 Safe"
    elif p <= 0.7: return "🟡 Medium"
    else: return "🔴 High"

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

    # Calculate student metrics
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
    else:
        student_clicks = 45.0
        student_score = 75.0

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
    else:
        cohort_clicks_avg = 52.0
        cohort_score_avg = 72.8

    # ROW A: KEY PERFORMANCE METRICS
    st.markdown('### Learning Key Metrics')
    col1, col2, col3 = st.columns(3)

    risk_pct = f"{prob * 100:.2f}%"
    risk_label = "Student Dropout Risk"
    if prob <= 0.3:
        status_label = "🟢 Safe"
    elif prob <= 0.7:
        status_label = "🟡 Warning"
    else:
        status_label = "🔴 Alert"
    col1.metric(risk_label, risk_pct, f"Status: {status_label} ({pred_class})")

    col2.metric("Cohort Average Risk", f"{cohort_risk_avg:.2f}%", f"Total: {len(df_filtered_risk)} Students")
    col3.metric("Student BKT Avg Mastery", f"{bkt_avg:.1f}%", f"Active Chapters: {len(bkt_mastery_dict)}")

    # ROW B: HEATMAP & PEER SCATTER PLOT
    c1, c2 = st.columns((6, 4))

    with c1:
        st.markdown('### BKT skill mastery Heatmap across Cohort Risk Groups')
        df_student_risk = df_filtered_risk[['student_id_hash', 'dropout_probability']].copy()
        df_student_risk['risk_band'] = df_student_risk['dropout_probability'].apply(get_risk_band)
        
        df_module_bkt_all = df_bkt[df_bkt['skill_name'].str.startswith(selected_module)]
        
        if not df_module_bkt_all.empty:
            df_bkt_merged = df_module_bkt_all.merge(df_student_risk, left_on='user_id', right_on='student_id_hash', how='inner')
            if not df_bkt_merged.empty:
                df_pivot = df_bkt_merged.groupby(['risk_band', 'skill_name'])['correct_predictions'].mean().unstack().fillna(0.0)
                render_cohort_heatmap(df_pivot, key_suffix="student_view")
            else:
                st.info("No matching BKT mastery data found for this cohort.")
        else:
            st.info(f"No BKT mastery records found matching module {selected_module}.")

    with c2:
        st.markdown('### Academic position vs Cohort')
        render_student_cohort_scatter(selected_student, df_cohort_module, student_clicks, student_score, key_suffix="student_view")

    # ROW C: CHECKPOINT TIMELINE & ENGAGEMENT GAUGE
    st.markdown('### Student Diagnostics & Timeline')
    col_c1, col_c2 = st.columns((6, 4))
    
    with col_c1:
        st.markdown("##### 📈 Longitudinal Checkpoint Timelines")
        df_timeline = get_student_timeline_data(selected_student, prob)
        render_student_timeline_plotly(df_timeline, key_suffix="student_view")
        
    with col_c2:
        st.markdown("##### ⚡ Student Engagement Peer Comparison")
        render_engagement_comparison(student_clicks, cohort_clicks_avg, key_suffix="student_clicks")

    # ROW D: RADAR PROFILE & RECOMMENDATIONS & PLAYGROUND
    st.markdown('### Adaptive Learning Sandboxes & Recommendations')
    col_d1, col_d2, col_d3 = st.columns((4, 4, 4))

    with col_d1:
        st.markdown("##### 🧠 Bayesian Knowledge Tracing Mastery Profile")
        if bkt_mastery_dict:
            render_student_radar(bkt_mastery_dict, key_suffix="student_radar")
        else:
            st.info("No chapter BKT mastery recorded yet for this student.")

    with col_d2:
        st.markdown('##### 🎯 Personalized Recommendations (LightGCN)')
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

    with col_d3:
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

    # ROW A: KEY PERFORMANCE METRICS
    st.markdown(f'### Universal Analytics KPIs — {scope_title}')
    col_u1, col_u2, col_u3 = st.columns(3)
    
    total_enrolled = len(df_univ_risk_merged)
    avg_univ_risk = df_univ_risk_merged['dropout_probability'].mean() * 100 if total_enrolled > 0 else 0.0
    avg_univ_mastery = df_univ_bkt['correct_predictions'].astype(float).mean() * 100 if not df_univ_bkt.empty else 67.8
    
    col_u1.metric("Total Cohort Size", f"{total_enrolled:,} Students")
    col_u2.metric("Cohort Average Risk", f"{avg_univ_risk:.2f}%")
    col_u3.metric("Cohort Average Mastery", f"{avg_univ_mastery:.1f}%")

    # ROW B: COMPREHENSIVE BKT HEATMAP & PEER SCATTER PLOT
    col_b1, col_b2 = st.columns((6, 4))
    
    with col_b1:
        st.markdown('### BKT skill mastery Heatmap across all Modules')
        if not df_univ_bkt.empty:
            df_bkt_all = df_univ_bkt.copy()
            df_bkt_all['module'] = df_bkt_all['skill_name'].apply(lambda x: x.split('_')[0] if '_' in x else 'Unknown')
            df_bkt_all['type'] = df_bkt_all['skill_name'].apply(lambda x: x.split('_')[1] if '_' in x else 'Unknown')
            df_pivot_all = df_bkt_all.groupby(['module', 'type'])['correct_predictions'].mean().unstack().fillna(0.0)
            render_cohort_heatmap(df_pivot_all, key_suffix="universal_view")
        else:
            st.info("No universal BKT records found.")

    with col_b2:
        st.markdown('### Cohort Score vs Clicks Distribution')
        render_universal_scatter(df_univ_risk_merged, key_suffix="universal")

    # ROW C: COMPREHENSIVE COHORT TIMELINE & VIOLIN DISTRIBUTION
    st.markdown('### Cohort Longitudinal Timeline & Variance')
    col_c1, col_c2 = st.columns((6, 4))
    
    with col_c1:
        st.markdown('##### Cohort Longitudinal Timeline (Average Performance)')
        df_cohort_timeline = get_student_timeline_data("cohort_average_seed", avg_univ_risk / 100.0)
        render_student_timeline_plotly(df_cohort_timeline, key_suffix="universal_view")
        
    with col_c2:
        st.markdown('##### Course Module Risk Variance (Box Distribution)')
        render_module_risk_violin(df_risk_merged, key_suffix="universal_box")

    # ROW D: DEMOGRAPHIC RISKS & FEATURE CORRELATIONS
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown('### Demographic Dropout Risk Tiers')
        demo_attr = st.selectbox(
            "Select Demographic Breakdown Attribute",
            ["highest_education", "gender", "age_band", "disability", "imd_band", "region"],
            index=0,
            key="univ_demo_selectbox"
        )
        render_demographic_risk_bars(df_univ_risk_merged, demo_attr, key_suffix="universal")

    with col_d2:
        st.markdown('### Behavioral Feature Correlation Heatmap')
        render_feature_correlation_heatmap(df_univ_risk_merged, key_suffix="universal")

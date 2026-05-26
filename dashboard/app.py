import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

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
    
    # Compute cohort-level metrics
    total_students = len(df_risk['student_id_hash'].unique())
    avg_risk = df_risk['dropout_probability'].mean() * 100
    
    stuck_skill_name = "N/A"
    stuck_skill_val = 0.0
    if not df_bkt.empty:
        try:
            df_bkt_clean = df_bkt.copy()
            df_bkt_clean['correct_predictions'] = df_bkt_clean['correct_predictions'].astype(float)
            skill_averages = df_bkt_clean.groupby('skill_name')['correct_predictions'].mean().reset_index()
            if not skill_averages.empty:
                lowest_skill = skill_averages.sort_values(by='correct_predictions').iloc[0]
                stuck_skill_name = lowest_skill['skill_name']
                stuck_skill_val = lowest_skill['correct_predictions']
        except Exception:
            pass

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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(fig_gender, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(fig_edu, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(fig_region, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

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
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.plotly_chart(fig_trend, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception:
                pass

# ==========================================
# TAB 2: STUDENT DEEP-DIVE (BẢN GỐC LÀM ĐẸP)
# ==========================================
with tab2:
    st.subheader(f"📊 Hồ sơ cá nhân học tập: {hash_to_friendly.get(selected_student)}")
    st.info(f"🔑 Định danh bảo mật (SHA-256 Cloud ID): `{selected_student}`")

    # ─── VIEW 1: CẢNH BÁO RỦI RO (LIGHTGBM) ───
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── VIEW 2: LỖ HỔNG KIẾN THỨC (pyBKT) ───
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

    # ─── VIEW 3: GỢI Ý TÀI LIỆU CÁ NHÂN HÓA (LIGHTGCN) ───
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 1rem 0;'>🎯 Gợi Ý Tài Liệu Học Tập Phù Hợp (LightGCN Đồ Thị Deep Learning)</h3>", unsafe_allow_html=True)
    
    # Calculate recommendations using Custom/Updated user embedding
    if st.session_state.custom_u_emb is not None:
        u_emb = st.session_state.custom_u_emb
        i_embs = np.stack(df_item_emb['item_embedding'].values)
        scores = np.dot(i_embs, u_emb)
        
        df_item_emb_scored = df_item_emb.copy()
        df_item_emb_scored['recommendation_score'] = scores
        top_5_items = df_item_emb_scored.sort_values(by='recommendation_score', ascending=False).head(5).copy()
        
        st.success("Hệ thống khuyên dùng 5 tài liệu học tập sau đây để bù đắp kiến thức:")
        top_5_items['recommendation_score'] = top_5_items['recommendation_score'].apply(lambda x: f"{x:.4f}")
        
        # Add Activity type to dataframe
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
    st.markdown('</div>', unsafe_allow_html=True)

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
                        st.session_state.interactions_log.append(f"🟢 [{t_now}] [Bronze/Silver] Clickstream logged: student={selected_student[:8]}..., site_id={site_id}")
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


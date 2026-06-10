# 🎓 B-LEARN: Hệ Thống Phân Tích & Cá Nhân Hóa Học Tập Thông Minh

**B-Learn** là một hệ thống DataOps quy mô đầy đủ (Production-Grade) được xây dựng trên nền tảng Azure AKS, tích hợp 3 mô hình AI học máy chuyên biệt để phân tích hành vi học tập, dự báo rủi ro bỏ học và gợi ý tài liệu học tập cá nhân hóa theo thời gian thực. Hệ thống xử lý dữ liệu từ 4 bộ dữ liệu giáo dục lớn (EdNet, OULAD, SED, Content) qua kiến trúc Medallion 3 tầng (Bronze → Silver → Gold) và phục vụ giao diện dashboard live qua Streamlit.

---

## 📐 Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAW DATA SOURCES                             │
│  EdNet (~4M events) │ OULAD (32K students) │ SED │ Content Datasets │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   🟤 BRONZE LAYER   │  Apache Iceberg on ADLS Gen2
                    │  full_db (Parquet)  │  Raw ingestion + audit metadata
                    └──────────┬──────────┘
                               │  PySpark Transform + SHA-256 Anonymization
                    ┌──────────▼──────────┐
                    │   ⚪ SILVER LAYER   │  Apache Iceberg on ADLS Gen2
                    │   silver_db         │  Cleaned, typed, anonymized tables
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
       │  LightGBM   │  │    pyBKT     │  │  LightGCN    │
       │  Risk Model │  │  Knowledge   │  │  RecSys      │
       │  (dropout%) │  │  Tracing     │  │  (Graph DL)  │
       └──────┬──────┘  └──────┬───────┘  └──────┬───────┘
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   🟡 GOLD LAYER     │  Apache Iceberg on ADLS Gen2
                    │   gold_db           │  Model outputs, embeddings
                    └──────────┬──────────┘
                               │  Export job (Spark → Parquet flat files)
                    ┌──────────▼──────────┐
                    │  🚀 SERVING LAYER   │  Azure Blob "serving" container
                    │  Parquet flat files │  NumPy dot-product (< 1ms)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ 📊 STREAMLIT UI     │  http://135.171.193.190
                    │  Live Dashboard     │  + NRT inference every 15min
                    └─────────────────────┘
```

---

## 🗂️ Cấu Trúc Repository

```
b-learn/
├── Dockerfile                          # Image cho AKS (python:3.12-slim + Java + PySpark)
├── Makefile                            # Tất cả lệnh tắt để chạy pipeline
├── README.md                           # Tài liệu này
│
├── data_pipeline/                      # Toàn bộ code pipeline
│   ├── requirements.txt                # Python dependencies
│   ├── ingestion/                      # Module Bronze ingestion
│   │   └── ingest.py                   # build_spark(), ghi Iceberg, kiểm thử
│   ├── silver/
│   │   └── oulad.py                    # Silver transform: SHA-256, ép kiểu, lọc
│   ├── gold/
│   │   └── oulad.py                    # Gold: feature engineering + LightGBM training
│   ├── jobs/                           # Các job chuyên dụng
│   │   ├── gold_bkt_pipeline.py        # Mô hình Bayesian Knowledge Tracing (pyBKT)
│   │   ├── gold_recsys_pipeline.py     # Hệ gợi ý LightGCN (PyTorch)
│   │   ├── export_to_serving.py        # Xuất Iceberg → Parquet Serving Layer
│   │   └── nrt_gold_inference.py       # Inference cận thời gian thực (15 phút/lần)
│   └── dags/
│       └── oulad_medallion_dag.py      # Apache Airflow DAG
│
├── dashboard/
│   └── app.py                          # Streamlit Dashboard (Glassmorphism UI)
│
├── infra/
│   ├── main.tf                         # Terraform: AKS, ACR, Storage, K8s secrets
│   ├── airflow-values.yaml             # Helm values: Airflow HA (KubernetesExecutor, 2 schedulers)
│   └── manifests/                      # Kubernetes manifests
│       ├── oulad-recsys-job.yaml       # One-shot Job: LightGCN training
│       ├── oulad-bkt-test.yaml         # One-shot Job: BKT test
│       ├── oulad-serving-export-job.yaml # One-shot Job: Export Parquet
│       ├── streamlit-dashboard.yaml    # Deployment + Service: Streamlit
│       ├── oulad-nrt-cronjob.yaml      # CronJob NRT: mỗi 15 phút
│       ├── oulad-bronze-cronjob.yaml   # CronJob Failover: 02:00 UTC daily
│       └── oulad-silver-cronjob.yaml   # CronJob Failover: 03:00 UTC daily
│
├── docs/
│   ├── medallion_architecture.md       # Tài liệu kiến trúc chi tiết
│   ├── bkt_pipeline_report.md          # Báo cáo phân tích BKT pipeline
│   └── guide-macos.md                  # Hướng dẫn chạy cục bộ trên macOS
│
└── .github/workflows/
    └── build-push-acr.yml              # GitHub Actions CI/CD: build + push image lên ACR
```

---

## 🧠 Ba Mô Hình AI Cốt Lõi

### 1. 🚨 LightGBM — Dự Báo Rủi Ro Bỏ Học

**File**: [`data_pipeline/gold/oulad.py`](data_pipeline/gold/oulad.py)

**Mục đích**: Phân loại sinh viên có nguy cơ bỏ học (Binary Classification) dựa trên hành vi tương tác với nền tảng VLE (Virtual Learning Environment).

**Đặc trưng đầu vào (Features)**:
- `num_of_prev_attempts` — Số lần thử trước đây
- `studied_credits` — Số tín chỉ đã học
- `total_clicks` — Tổng số lượt click vào tài liệu
- `active_days` — Số ngày hoạt động
- `avg_daily_clicks` — Trung bình click hàng ngày
- `max_clicks_day` — Ngày click nhiều nhất
- `engagement_span` — Khoảng thời gian hoạt động
- `recent_weekly_rate` — Tỉ lệ tương tác tuần gần nhất
- `recency_days` — Số ngày kể từ lần cuối hoạt động
- `engagement_momentum` — Động lượng tương tác
- `avg_score`, `min_score` — Điểm số trung bình / thấp nhất

**Đầu ra vào Gold Iceberg**:
- Bảng: `gold_catalog.gold_db.oulad_at_risk_predictions`
- Cột quan trọng: `student_id_hash`, `dropout_probability`, `predicted_class`

**Mô hình artifact**: Lưu lên Azure Blob `models/oulad_lgbm_pipeline.joblib`

---

### 2. 🧠 pyBKT — Đo Lường Kiến Thức Bayesian (BKT)

**File**: [`data_pipeline/jobs/gold_bkt_pipeline.py`](data_pipeline/jobs/gold_bkt_pipeline.py)

**Mục đích**: Áp dụng chuỗi Markov ẩn (HMM) để theo dõi trạng thái thành thục kiến thức (Knowledge Mastery) của sinh viên qua từng bài kiểm tra tuần tự.

**Thuật toán**: Bayesian Knowledge Tracing (BKT) — dựa trên 4 tham số cốt lõi:
- `p_learn` — Xác suất học được kiến thức mới
- `p_slip` — Xác suất mắc lỗi dù đã biết
- `p_guess` — Xác suất đoán đúng dù chưa biết
- `p_init` — Xác suất đã biết từ trước

**Dữ liệu đầu vào** (từ Silver Layer, chỉ khóa học **AAA** của OULAD để bảo toàn chuỗi tuần tự):
- `oulad_assessments` — Danh sách bài kiểm tra và loại hình
- `oulad_student_assessment` — Kết quả điểm số của từng sinh viên

**Đầu ra vào Gold Iceberg**:
- Bảng: `gold_catalog.gold_db.oulad_bkt_mastery`
- Cột quan trọng: `user_id`, `skill_name`, `correct_predictions`

---

### 3. 🎯 LightGCN — Hệ Gợi Ý Tài Liệu (Graph Deep Learning)

**File**: [`data_pipeline/jobs/gold_recsys_pipeline.py`](data_pipeline/jobs/gold_recsys_pipeline.py)

**Mục đích**: Sử dụng kiến trúc đồ thị học sâu LightGCN (Light Graph Convolutional Network) để học ra các vector nhúng (Embeddings) đặc trưng cho từng sinh viên và tài liệu học tập, từ đó tính điểm tương đồng và đề xuất 5 tài liệu phù hợp nhất.

**Kiến trúc**:
- 64 chiều embedding (`d_dim=64`)
- 3 lớp Graph Convolution (`layers=3`)
- Hàm tối ưu: BPR Loss (Bayesian Personalized Ranking)
- 10 epochs huấn luyện
- Bộ lọc nhiễu: `percentile_approx(sum_click, 0.5)` loại bỏ tương tác yếu

**Đầu ra vào Gold Iceberg**:
- Bảng user embeddings: `gold_catalog.gold_db.oulad_recsys_user_embeddings` — **25,166 sinh viên**
- Bảng item embeddings: `gold_catalog.gold_db.oulad_recsys_item_embeddings` — **6,268 tài liệu**

---

## ⚡ Kiến Trúc Hybrid: Offline Training + NRT Inference

Đây là thiết kế cốt lõi tránh anti-pattern "train lại liên tục":

| Layer | Tần suất | Job thực hiện |
|-------|----------|---------------|
| **Offline Training** | Mỗi 12h (03:00 UTC) | `gold_recsys_pipeline.py`, `gold_bkt_pipeline.py`, `gold/oulad.py` |
| **NRT Inference** | Mỗi 15 phút | `nrt_gold_inference.py` |

**File NRT**: [`data_pipeline/jobs/nrt_gold_inference.py`](data_pipeline/jobs/nrt_gold_inference.py)

**Luồng NRT** (không train lại):
1. Đọc các sự kiện tương tác **mới nhất** trong cửa sổ 15 phút từ Silver
2. Nạp **frozen embeddings** đã được huấn luyện từ đêm (Gold Iceberg)
3. Tính `item_matrix @ u_vec` (NumPy dot-product, < 1ms)
4. Ghi kết quả ra `nrt_recommendations.parquet` trên Serving Layer
5. Tự động thoát sớm nếu không có sự kiện mới (`Exiting early`)

**Tài nguyên NRT Pod**: `requests.cpu=200m, memory=1Gi` — cực kỳ tiết kiệm cho AKS node giá rẻ.

---

## 🏗️ Hạ Tầng Azure

### Terraform (`infra/main.tf`)

Toàn bộ hạ tầng được quản lý bởi **Terraform** với remote state lưu trên Azure Storage:

| Tài nguyên | Tên | Mô tả |
|-----------|-----|-------|
| Resource Group | `RG-BLEarn-Compute` | Nhóm tài nguyên chính (Southeast Asia) |
| Storage Account | `stblearnminhdata2026` | Chứa các container Medallion layers |
| Storage Container | `bronze`, `silver`, `gold`, `serving` | Các tầng Iceberg warehouse |
| AKS Cluster | `aks-blearn-dev` | 2 nodes `Standard_D8s_v3`, network plugin Azure |
| ACR | `acrblearnminh2026` | Azure Container Registry (SKU: Basic) |
| K8s Namespace | `blearn-medallion` | Namespace chạy tất cả jobs |
| K8s Secret | `oulad-runtime` | Chứa `AZURE_STORAGE_ACCOUNT` và `AZURE_STORAGE_KEY` |
| K8s CronJob | `oulad-medallion-pipeline` | Pipeline chính (03:00 UTC, `Forbid` concurrency) |

**Lệnh Terraform**:
```bash
cd infra
terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform output -raw storage_account_key  # Lấy key lưu vào GitHub Secret
```

### Kubernetes Namespace & Secret

```bash
# Namespace đã được Terraform tạo sẵn, nhưng nếu cần tạo thủ công:
kubectl create namespace blearn-medallion

# Tạo secret thủ công (khi không dùng Terraform)
kubectl create secret generic oulad-runtime \
  --from-literal=AZURE_STORAGE_ACCOUNT=stblearnminhdata2026 \
  --from-literal=AZURE_STORAGE_KEY="<your-key>" \
  -n blearn-medallion
```

### Docker Image & CI/CD

**File**: [`.github/workflows/build-push-acr.yml`](.github/workflows/build-push-acr.yml)

CI/CD tự động build và push Docker image khi có push lên nhánh `main`:
- Runner: `ubuntu-latest`
- Target platform: `linux/amd64` (bắt buộc để chạy trên AKS, tránh lỗi ARM64 của Apple Silicon)
- Registry: `acrblearnminh2026.azurecr.io/oulad-medallion:latest`
- Cache: GitHub Actions cache (`type=gha`)

**GitHub Secrets cần thiết**:
- `ACR_NAME` — tên ACR (vd: `acrblearnminh2026`)
- `ACR_USERNAME` — admin username của ACR
- `ACR_PASSWORD` — admin password của ACR

**Build thủ công khi cần (Apple Silicon → AKS)**:
```bash
# Build cho linux/amd64 (bắt buộc khi build từ Mac M-series)
docker build --platform linux/amd64 \
  -t acrblearnminh2026.azurecr.io/oulad-medallion:latest .
az acr login --name acrblearnminh2026
docker push acrblearnminh2026.azurecr.io/oulad-medallion:latest
```

---

## 🛠️ Thiết Lập Môi Trường & Chạy Dịch Vụ

### 🔑 Yêu Cầu Credentials & Biến Môi Trường

Để chạy các dịch vụ và kết nối hạ tầng Azure Cloud hoặc Kafka/Redis, bạn cần cấu hình các biến môi trường sau:

```bash
# ☁️ Azure Storage Credentials (Cần thiết để đọc ghi các bảng Iceberg/Parquet trên ADLS Gen2)
export AZURE_STORAGE_ACCOUNT=stblearnminhdata2026
export AZURE_STORAGE_KEY="<your-azure-storage-key>" # Lấy từ Azure portal (Access keys)

# 🔐 JWT Authentication (Dùng cho API Gateway phục vụ bảo mật)
export JWT_SECRET_KEY="b-learn-super-secret-key-1015" # Key dùng để ký token
export CORS_ALLOW_ORIGINS="*" # Cho phép truy cập CORS từ frontend

# 📡 Real-time Event Streaming (Kafka & Redis)
export KAFKA_BOOTSTRAP_SERVERS="kafka-service.blearn-medallion.svc.cluster.local:9092" # Hoặc localhost:9092 khi chạy local
export KAFKA_TOPIC="learning-events"
export CLICK_FALLBACK_LOG_PATH="/tmp/fallback_clicks.log" # Đường dẫn ghi log dự phòng khi Kafka down

# ⚙️ Tùy chọn Spark & NRT
export SPARK_DRIVER_MEMORY=8g     # Mặc định: 8g (local), 3g-5g (AKS)
export NRT_WINDOW_MINUTES=15      # Cửa sổ thời gian NRT (phút)
```

> [!NOTE]
> Nếu bạn không cung cấp `AZURE_STORAGE_KEY`, các dịch vụ API Gateway và Streamlit sẽ tự động fallback đọc dữ liệu Parquet từ các Public URL của Azure Storage hoặc từ các file lưu trữ cục bộ sẵn trong thư mục dự án.

---

### 💻 Hướng Dẫn Chạy Các Dịch Vụ Dưới Local

#### 1. FastAPI Serving Gateway (Backend API)
Serving Gateway quản lý xác thực JWT, nhận clickstream, thực hiện Bayesian BKT và live inference LightGBM thời gian thực.

```bash
# Đảm bảo virtual environment đã được kích hoạt và cài dependencies
source .venv/bin/activate
pip install -r data_pipeline/requirements.txt

# Khởi chạy Serving Gateway
uvicorn backend-api.serving_gateway:app --host 0.0.0.0 --port 8000 --reload
```
API sẽ hoạt động tại `http://localhost:8000`. Bạn có thể truy cập `/docs` để xem tài liệu Swagger API chi tiết.

#### 2. React Frontend Demo
Giao diện trực quan tích hợp giả lập LMS và luồng adaptive learning.

```bash
cd frontend-demo

# Cấu hình biến môi trường kết nối API Gateway (Tạo file .env)
echo "VITE_GATEWAY_URL=http://localhost:8000" > .env

# Cài đặt thư viện và khởi chạy
npm install
npm run dev
```
Giao diện demo sẽ chạy tại `http://localhost:5173`.

#### 3. Streamlit Dashboard (Cohort Analytics UI)
Dashboard thống kê tổng quan toàn khóa học và chi tiết hồ sơ cá nhân.

```bash
# Chạy Dashboard từ thư mục root của dự án
streamlit run dashboard/app.py
```
Streamlit UI sẽ chạy tại `http://localhost:8501`.

---

### 🍎 Cài Đặt Môi Trường Phát Triển Cục Bộ (macOS)

Xem hướng dẫn chi tiết tại [`docs/guide-macos.md`](docs/guide-macos.md).

```bash
# Cài đặt Java 17 (Bắt buộc cho PySpark)
brew install openjdk@17

# Tạo virtual environment và cài đặt các thư viện cần thiết
python3 -m venv .venv
source .venv/bin/activate
pip install -r data_pipeline/requirements.txt

# Cấu hình AKS credentials (nếu cần tương tác cụm Kubernetes)
az aks get-credentials --resource-group RG-BLEarn-Compute --name aks-blearn-dev
```

---

## 📦 Python Dependencies

File: [`data_pipeline/requirements.txt`](data_pipeline/requirements.txt)

| Package | Phiên bản | Mục đích |
|---------|-----------|----------|
| `pyspark` | 3.5.1 | Xử lý dữ liệu phân tán, đọc/ghi Iceberg |
| `numpy` | ≥1.26 | Ma trận nhúng, dot-product NRT inference |
| `pandas` | ≥2.2 | Xử lý DataFrame trên driver |
| `scikit-learn` | 1.3.2 | Pipeline preprocessing, metrics |
| `lightgbm` | ≥4.3 | Mô hình phân loại rủi ro bỏ học |
| `joblib` | ≥1.3 | Lưu/tải model artifact |
| `azure-storage-blob` | ≥12.20 | Kết nối Azure Blob Storage |
| `pyBKT` | 1.3.0 | Bayesian Knowledge Tracing |
| `torch` | 2.2.0 (CPU) | LightGCN Graph Neural Network |
| `streamlit` | 1.32.0 | Dashboard UI |
| `adlfs` | 2024.4.0 | Đọc Parquet trực tiếp từ ADLS Gen2 |

**Lưu ý**: Apache Iceberg runtime được nạp qua Maven tại runtime (`spark.jars.packages`), không cài qua pip.

---

## 🔄 Quy Trình Chạy Pipeline (End-to-End)

### Tầng Bronze (Ingestion)

```bash
# Bước 1: Consolidate EdNet CSVs thành Parquet groups (cần chạy 1 lần duy nhất)
make bronze-consolidate-ednet

# Bước 2: Tạo manifest JSON liệt kê tất cả file nguồn
make bronze-full-manifest

# Bước 3: Nạp dữ liệu vào Iceberg (ADLS Gen2)
SPARK_DRIVER_MEMORY=8g AZURE_STORAGE_KEY="<key>" make bronze-full-ingest

# Bước 4: Kiểm tra số dòng giữa nguồn và đích
make bronze-full-verify

# Bước 5: Audit metadata columns để đảm bảo chất lượng
make bronze-full-audit

# Chạy toàn bộ Bronze flow một lần
SPARK_DRIVER_MEMORY=8g AZURE_STORAGE_KEY="<key>" make bronze-full-flow
```

**Output**: `abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/full/`

---

### Tầng Silver (Transform & Anonymize)

```bash
# Transform OULAD Bronze → Silver (SHA-256, ép kiểu, lọc outlier)
AZURE_STORAGE_KEY="<key>" make silver-run
```

**Thao tác thực hiện**:
- Đọc từ `bronze_catalog.full_db.*`
- Băm hóa `id_student` → `student_id_hash` bằng SHA-256
- Ép kiểu, loại bỏ NULL, chuẩn hóa cột
- Ghi vào `silver_catalog.silver_db.*` trên ADLS Gen2

**Output**: `abfss://silver@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/silver/`

---

### Tầng Gold (Feature Engineering + AI Models)

```bash
# Chạy LightGBM (Risk Prediction)
AZURE_STORAGE_KEY="<key>" make gold-lgbm-run

# Chạy BKT (Knowledge Tracing)
AZURE_STORAGE_KEY="<key>" make gold-bkt-run

# Chạy LightGCN RecSys (Recommendation)
AZURE_STORAGE_KEY="<key>" make gold-recsys-run
```

**Output**: `abfss://gold@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/gold/`

---

### Serving Layer (Export Parquet)

```bash
# Chạy cục bộ
AZURE_STORAGE_KEY="<key>" make serving-export-run

# Chạy trên AKS cluster
make k8s-serving-export
```

**Output files** vào `abfss://serving@stblearnminhdata2026.dfs.core.windows.net/ui_data/`:
- `risk_predictions.parquet` — LightGBM dropout predictions
- `bkt_mastery.parquet` — pyBKT mastery scores per student
- `user_embeddings.parquet` — LightGCN user vectors (25,166 rows)
- `item_embeddings.parquet` — LightGCN item vectors (6,268 rows)
- `nrt_recommendations.parquet` — NRT real-time recommendations (cập nhật mỗi 15 phút)

---

### Dashboard Streamlit

```bash
# Chạy cục bộ
AZURE_STORAGE_KEY="<key>" make streamlit-local-run

# Deploy lên AKS
make k8s-deploy-streamlit

# Xem IP Public
make k8s-streamlit-status
```

**URL Live**: http://135.171.193.190

---

## ⚡ NRT Inference (Cận Thời Gian Thực)

```bash
# Chạy thủ công cục bộ (test nhanh)
AZURE_STORAGE_KEY="<key>" make nrt-inference-run

# Deploy CronJob NRT lên AKS (mỗi 15 phút tự động)
make k8s-deploy-nrt

# Trigger NRT ngay lập tức (manual test 1 lần)
make k8s-nrt-trigger-once
```

**Luồng hoạt động**:
```
NRT Job (mỗi 15 phút)
  ├─ Load frozen embeddings từ Gold Iceberg (không train lại)
  ├─ Scan Silver: có sự kiện mới trong 15 phút qua?
  │   ├─ Không có → Thoát sớm (Exiting early), tiết kiệm 100% CPU
  │   └─ Có → Chạy NumPy dot-product cho các sinh viên vừa hoạt động
  └─ Ghi nrt_recommendations.parquet lên Serving Layer
```

---

## 🛡️ Hệ Thống Chịu Lỗi & Dự Phòng (Failover)

Kiến trúc **Active-Passive**: Airflow là Primary, K8s Native CronJobs là Passive.

### Kịch Bản Airflow Lỗi → Kích Hoạt Failover

```bash
# Kích hoạt toàn bộ lịch K8s thay thế Airflow
make k8s-activate-failover-schedule

# Kết quả: 3 CronJobs được arm
#   • oulad-bronze-cronjob     → 02:00 UTC daily  (Bronze ingestion)
#   • oulad-silver-gold-cronjob → 03:00 UTC daily  (Silver + Gold full training chain)
#   • oulad-nrt-cronjob        → */15 * * * *     (NRT inference)

# Kiểm tra trạng thái
make k8s-failover-status
```

### Khi Airflow Phục Hồi → Tắt Failover

```bash
# Tắt Bronze + Silver-Gold CronJobs (giữ NRT)
make k8s-deactivate-failover-schedule

# NRT CronJob giữ nguyên — chạy song song với Airflow là an toàn
```

---

## 🏗️ Airflow High Availability (HA)

Cấu hình nâng cấp Airflow từ `LocalExecutor` lên `KubernetesExecutor + 2 Schedulers`:

**File**: [`infra/airflow-values.yaml`](infra/airflow-values.yaml)

```bash
# Áp dụng cấu hình HA mới
make airflow-upgrade-ha

# Kiểm tra schedulers
kubectl get pods -n blearn-medallion -l component=scheduler
```

**Thay đổi cốt lõi**:
| Thuộc tính | Trước | Sau |
|-----------|-------|-----|
| Executor | `LocalExecutor` | `KubernetesExecutor` |
| Schedulers | 1 replica | **2 replicas (Active-Active HA)** |
| Task isolation | Process-level | **Pod-level (K8s Pod per Task)** |

---

## 📊 Airflow DAG

**File**: [`data_pipeline/dags/oulad_medallion_dag.py`](data_pipeline/dags/oulad_medallion_dag.py)

DAG `oulad_medallion_pipeline` (on-demand, `schedule=None`):

```
bronze_ingest → silver_transform → gold_feature_model
```

Mỗi Task chạy trong Pod K8s riêng biệt (`KubernetesPodOperator`). Credentials được inject từ K8s Secret `oulad-runtime`.

**Triển khai DAG**:
```bash
# DAG được inject vào Airflow qua ConfigMap
kubectl create configmap oulad-medallion-dag \
  --from-file=data_pipeline/dags/oulad_medallion_dag.py \
  -n blearn-medallion
```

---

## 🖥️ Dashboard Streamlit

**File**: [`dashboard/app.py`](dashboard/app.py)

### Cấu Trúc 3 Phân Hệ (Tabs)

| Phân hệ (Tab) | Mô tả | Chi tiết kỹ thuật |
|---|---|---|
| **Tab 1: 📈 Tổng Quan (Cohort Analytics)** | Giao diện quản lý học đường (BI) của toàn trường học | - KPI Cards: Tổng số học viên, tỷ lệ rủi ro trung bình, kỹ năng gây kẹt nhất (pyBKT).<br>- Plotly Pie Chart: Phân phối giới tính.<br>- Plotly Bar Chart: Trình độ học vấn & Top 8 vùng miền.<br>- Plotly Line Chart: Xu hướng click chuột trung bình theo tuần học. |
| **Tab 2: 👤 Hồ Sơ Cá Nhân (Student Deep-Dive)** | Phân tích chi tiết rủi ro và học tập của từng học viên được chọn ở Sidebar | - Cảnh báo rủi ro bỏ học (LightGBM).<br>- Trạng thái thành thục 7 kỹ năng (pyBKT).<br>- Đề xuất top 5 tài liệu học tập phù hợp (LightGCN). |
| **Tab 3: 🎮 Giả Lập LMS (External App Integration)** | Mô phỏng tương tác của sinh viên trên nền tảng học trực tuyến | - Cho phép bấm nút học tập các tài liệu đề xuất.<br>- Cập nhật Vector nhúng thời gian thực (in-memory embedding update) dịch chuyển vector học viên hướng tới tài liệu đã học: $u_{new} = u_{old} + 0.3 \cdot i_{clicked}$.<br>- Tự động re-calculate gợi ý mới tức thì (Real-time Adaptive Learning).<br>- Hiện thị console logs luồng xử lý NRT (Bronze → Silver → Gold NRT → Serving). |

### Design System & Performance

- **Font & Theme**: Google Fonts Outfit (300/400/600/700) + Glassmorphism dark mode (`rgba(255, 255, 255, 0.05)`, `backdrop-filter: blur(12px)`).
- **Trực quan hóa**: Sử dụng thư viện Plotly Express cho các biểu đồ tương tác mượt mà, bóng bẩy.
- **Hiệu suất**: Đọc trực tiếp các tệp Parquet từ Azure ADLS Gen2 (`cohort_stats.parquet`, `lms_simulator.parquet`, `risk_predictions.parquet`, `bkt_mastery.parquet`, `user_embeddings.parquet`, `item_embeddings.parquet`) bằng `@st.cache_data`. Gợi ý dot-product chạy bằng NumPy trên CPU chỉ mất **< 1ms**.


---

## 🔧 Tất Cả Lệnh Makefile

### Bronze (Ingestion)

```bash
make bronze-consolidate-ednet    # Compact EdNet CSVs → Parquet groups
make bronze-full-manifest        # Build full_data_manifest.json
make bronze-full-ingest          # Load manifest → Iceberg bronze
make bronze-full-verify          # Cross-check nguồn vs Bronze row counts
make bronze-full-audit           # Sample audit metadata columns
make bronze-full-flow            # Chạy toàn bộ chuỗi Bronze
```

### Silver & Gold (Local)

```bash
make silver-run                  # OULAD Bronze → Silver (SHA-256, transform)
make gold-lgbm-run               # Chạy LightGBM risk model
make gold-bkt-run                # Chạy pyBKT knowledge tracing model
make gold-recsys-run             # Chạy LightGCN recommendation model
make serving-export-run          # Xuất Gold → Parquet Serving Layer
make streamlit-local-run         # Khởi động Streamlit dashboard locally
```

### NRT (Near-Real-Time)

```bash
make nrt-inference-run           # Chạy NRT inference thủ công (cục bộ)
make k8s-deploy-nrt              # Deploy CronJob NRT lên AKS (*/15 * * * *)
make k8s-nrt-trigger-once        # Trigger NRT job ngay lập tức trên AKS
```

### Kubernetes (AKS)

```bash
make k8s-test-bkt                # Kích hoạt test BKT job trên AKS + xem log
make k8s-serving-export          # Trigger Serving Export job trên AKS + xem log
make k8s-deploy-streamlit        # Deploy Streamlit dashboard lên AKS
make k8s-streamlit-status        # Xem IP LoadBalancer của Streamlit
make k8s-clean-test              # Xóa tất cả Job tạm thời trong namespace
```

### Failover & HA

```bash
make k8s-activate-failover-schedule    # Arm K8s CronJobs khi Airflow lỗi
make k8s-deactivate-failover-schedule  # Disarm khi Airflow phục hồi
make k8s-failover-status               # Kiểm tra trạng thái tất cả CronJobs
make airflow-upgrade-ha                # Helm upgrade: KubernetesExecutor + 2 Schedulers
```

### Pipeline Full (Local)

```bash
make pipeline-full-local         # Bronze → Silver → LightGBM → BKT (toàn cục bộ)
```

---

## 🔧 K8s Manifests Chi Tiết

### NRT CronJob (`oulad-nrt-cronjob.yaml`)

```yaml
schedule: "*/15 * * * *"
concurrencyPolicy: Forbid      # Bỏ qua nếu job cũ chưa xong
backoffLimit: 0                # Không retry, đợi lần tiếp theo
resources:
  requests:
    cpu: "200m"
    memory: "1Gi"
```

### Bronze Failover CronJob (`oulad-bronze-cronjob.yaml`)

```yaml
schedule: "0 2 * * *"         # 02:00 UTC hàng ngày
concurrencyPolicy: Forbid
```

### Silver-Gold Failover CronJob (`oulad-silver-cronjob.yaml`)

```yaml
schedule: "0 3 * * *"         # 03:00 UTC hàng ngày
# Chains: silver.oulad → gold.oulad → gold_bkt_pipeline → gold_recsys_pipeline → export_to_serving
```

### Streamlit Deployment (`streamlit-dashboard.yaml`)

```yaml
command: ["streamlit", "run", "/app/dashboard/app.py",
          "--server.port=8501", "--server.address=0.0.0.0"]
# Service: LoadBalancer, port 80 → targetPort 8501
# External IP: 135.171.193.190
```

---

## 🧪 Kết Quả Kiểm Thử End-to-End (E2E Validation)

Tất cả 5 giai đoạn kiểm thử đã được thực hiện trực tiếp trên cụm AKS:

| Giai đoạn | Nội dung | Kết quả |
|-----------|----------|---------|
| **G1** — Xác thực Image | Restart Streamlit + Deploy NRT CronJob | ✅ Pod Rolling update thành công |
| **G2** — Batch Serving Export | Trigger `oulad-serving-export-job` | ✅ Hoàn thành trong **75 giây**, 4 file Parquet ghi thành công |
| **G3** — NRT Inference | Trigger `nrt-manual-xxx` job | ✅ Load **25,166 users / 6,268 items** embeddings, thoát sớm khi không có event mới |
| **G4** — Dashboard Live | Kiểm tra http://135.171.193.190 | ✅ IP Public khớp, UI hoạt động đúng |
| **G5** — Failover | `make k8s-activate-failover-schedule` | ✅ 3 CronJobs `SUSPEND=False`, sẵn sàng gánh tải |

---

## 🔍 Troubleshooting

### Lỗi Platform Mismatch (Apple Silicon → AKS)

```
Error: no match for platform in manifest: not found
```

**Nguyên nhân**: Docker build trên Mac M-series tạo image `linux/arm64`, AKS cần `linux/amd64`.

**Giải pháp**:
```bash
docker build --platform linux/amd64 \
  -t acrblearnminh2026.azurecr.io/oulad-medallion:latest .
docker push acrblearnminh2026.azurecr.io/oulad-medallion:latest
kubectl rollout restart deployment/blearn-streamlit-ui -n blearn-medallion
```

### Lỗi Dashboard Crash: `File does not exist: dashboard/app.py`

**Nguyên nhân**: `Dockerfile` không copy thư mục `dashboard/`.

**Giải pháp**: Đã thêm vào Dockerfile:
```dockerfile
COPY dashboard/ /app/dashboard/
```
Và cập nhật manifest dùng absolute path:
```yaml
command: ["streamlit", "run", "/app/dashboard/app.py", ...]
```

### AKS Pod OOMKilled (Out of Memory)

**Nguyên nhân**: CPU limit quá thấp so với nhu cầu Spark.

**Giải pháp**: Tăng `requests.cpu` đảm bảo ≤ 1.8 (giới hạn của Azure Student node):
```yaml
resources:
  requests:
    cpu: "800m"    # Spark jobs
  limits:
    cpu: "1.5"
```

### Airflow "has no deployed releases"

**Nguyên nhân**: Airflow chưa được cài bằng Helm hoặc đã bị xóa.

**Giải pháp**: Dùng K8s Native CronJob failover thay thế:
```bash
make k8s-activate-failover-schedule
```

---

## 📚 Tài Liệu Bổ Sung

- [📖 Medallion Architecture](docs/medallion_architecture.md) — Chi tiết Bronze consolidation, Silver anonymization, LightGBM feature engineering, AKS cluster infra
- [📊 BKT Pipeline Report](docs/bkt_pipeline_report.md) — Root-cause analysis: pyBKT memory bottlenecks, parameter tuning, sequential iterator loop
- [🍎 macOS Setup Guide](docs/guide-macos.md) — Hướng dẫn cài đặt và chạy cục bộ trên macOS

---

## 📋 Dataset Nguồn

| Dataset | Nội dung | Kích thước ước tính |
|---------|----------|---------------------|
| **EdNet** (KT1/KT2/KT4) | Tương tác học sinh với bài tập online | ~4M sự kiện |
| **OULAD** | Dữ liệu học tập mở của Đại học Mở (UK) | ~32K sinh viên |
| **SED** | Dữ liệu giáo dục bổ sung | — |
| **Content** | Siêu dữ liệu nội dung tài liệu | — |

---

## 🌐 Thông Tin Hệ Thống Live

| Thành phần | Địa chỉ / Tên |
|-----------|---------------|
| Streamlit Dashboard | http://135.171.193.190 |
| Azure Storage Account | `stblearnminhdata2026` |
| Azure Container Registry | `acrblearnminh2026.azurecr.io` |
| AKS Cluster | `aks-blearn-dev` (Southeast Asia) |
| K8s Namespace | `blearn-medallion` |
| GitHub Repository | https://github.com/minhtran1015/b-learn |

---

*Hệ thống được xây dựng cho mục đích nghiên cứu và giảng dạy, áp dụng các nguyên tắc DataOps và MLOps hiện đại.*
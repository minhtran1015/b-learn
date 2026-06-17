# B-LEARN: Hệ Thống Phân Tích & Cá Nhân Hóa Học Tập

**B-Learn** là một hệ thống DataOps trên nền tảng Azure AKS, tích hợp 3 mô hình học máy để phân tích hành vi học tập, dự báo rủi ro bỏ học và gợi ý tài liệu học tập cá nhân hóa theo thời gian thực. Hệ thống xử lý dữ liệu từ EdNet, OULAD, SED, và Content qua kiến trúc Medallion 3 tầng (Bronze → Silver → Gold) và phục vụ giao diện dashboard qua Streamlit.

---

## Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAW DATA SOURCES                             │
│  EdNet (~4M events) │ OULAD (32K students) │ SED │ Content Datasets │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     BRONZE LAYER    │  Apache Iceberg on ADLS Gen2
                    │  full_db (Parquet)  │  Raw ingestion + audit metadata
                    └──────────┬──────────┘
                               │  PySpark Transform + SHA-256 Anonymization
                    ┌──────────▼──────────┐
                    │     SILVER LAYER    │  Apache Iceberg on ADLS Gen2
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
                    │      GOLD LAYER     │  Apache Iceberg on ADLS Gen2
                    │   gold_db           │  Model outputs, embeddings
                    └──────────┬──────────┘
                               │  Export job (Spark → Parquet flat files)
                    ┌──────────▼──────────┐
                    │    SERVING LAYER    │  Azure Blob "serving" container
                    │  Parquet flat files │  NumPy dot-product (< 1ms)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     STREAMLIT UI    │  http://135.171.193.190
                    │  Live Dashboard     │  + NRT inference every 15min
                    └─────────────────────┘
```

---

## Cấu Trúc Thư Mục

```
b-learn/
├── Dockerfile                          # Image cho AKS (python:3.12-slim + Java + PySpark)
├── Makefile                            # Các lệnh quản lý dự án
├── README.md                           # Tài liệu hướng dẫn
│
├── data_pipeline/                      # Pipeline xử lý dữ liệu
│   ├── requirements.txt                # Các thư viện Python
│   ├── ingestion/                      # Module Bronze ingestion
│   │   └── ingest.py                   # build_spark(), ghi Iceberg, kiểm thử
│   ├── silver/
│   │   └── oulad.py                    # Silver transform: SHA-256, ép kiểu, lọc
│   ├── gold/
│   │   └── oulad.py                    # Gold: feature engineering + LightGBM training
│   ├── jobs/                           # Các job Spark và inference
│   │   ├── gold_bkt_pipeline.py        # Mô hình Bayesian Knowledge Tracing (pyBKT)
│   │   ├── gold_recsys_pipeline.py     # Hệ gợi ý LightGCN (PyTorch)
│   │   ├── export_to_serving.py        # Xuất Iceberg → Parquet Serving Layer
│   │   └── nrt_gold_inference.py       # Inference cận thời gian thực (15 phút/lần)
│   └── dags/
│   │   └── oulad_medallion_dag.py      # Apache Airflow DAG
│   └── utils/
│
├── dashboard/
│   └── app.py                          # Streamlit Dashboard
│
├── infra/
│   ├── main.tf                         # Terraform cấu hình tài nguyên Azure
│   ├── airflow-values.yaml             # Cấu hình Helm chart Airflow
│   └── manifests/                      # Kubernetes manifests
│       ├── oulad-recsys-job.yaml       # Job train LightGCN
│       ├── oulad-bkt-test.yaml         # Job test BKT
│       ├── oulad-serving-export-job.yaml # Job xuất dữ liệu phục vụ
│       ├── streamlit-dashboard.yaml    # Deployment và Service cho Streamlit
│       ├── oulad-nrt-cronjob.yaml      # CronJob chạy NRT Inference
│       ├── oulad-bronze-cronjob.yaml   # CronJob nạp Bronze hàng ngày
│       └── oulad-silver-cronjob.yaml   # CronJob nạp Silver hàng ngày
│
├── docs/
│   ├── medallion_architecture.md       # Tài liệu kiến trúc Medallion
│   ├── bkt_pipeline_report.md          # Phân tích BKT pipeline
│   └── guide-macos.md                  # Hướng dẫn chạy cục bộ trên macOS
│
└── .github/workflows/
    └── build-push-acr.yml              # GitHub Actions CI/CD
```

---

## Các Mô Mô Hình Học Máy

### LightGBM - Dự Báo Rủi Ro Bỏ Học

**File**: [`data_pipeline/gold/oulad.py`](data_pipeline/gold/oulad.py)

**Mục đích**: Phân loại học viên có nguy cơ bỏ học dựa trên tương tác với hệ thống.

**Đặc trưng đầu vào (Features)**:
- `num_of_prev_attempts` — Số lần học lại trước đây
- `studied_credits` — Số tín chỉ đang đăng ký
- `total_clicks` — Tổng số tương tác (click)
- `active_days` — Số ngày hoạt động trên hệ thống
- `avg_daily_clicks` — Số lượt tương tác trung bình ngày
- `max_clicks_day` — Lượt tương tác cao nhất trong một ngày
- `engagement_span` — Khoảng thời gian từ lần đầu tới lần cuối hoạt động
- `recent_weekly_rate` — Tần suất hoạt động tuần gần nhất
- `recency_days` — Số ngày không hoạt động gần đây
- `engagement_momentum` — Động lượng hoạt động học tập
- `avg_score`, `min_score` — Điểm số đánh giá trung bình và tối thiểu

**Đầu ra Gold Iceberg**:
- Bảng: `gold_catalog.gold_db.oulad_at_risk_predictions`
- Cột chính: `student_id_hash`, `dropout_probability`, `predicted_class`

**Model artifact**: Lưu trên Azure Blob `models/oulad_lgbm_pipeline.joblib`

---

### pyBKT - Theo Dõi Trạng Thái Kiến Thức

**File**: [`data_pipeline/jobs/gold_bkt_pipeline.py`](data_pipeline/jobs/gold_bkt_pipeline.py)

**Mục đích**: Áp dụng mô hình Bayesian Knowledge Tracing để theo dõi mức độ hiểu bài của học viên qua các bài kiểm tra tuần tự.

**Tham số cốt lõi**:
- `p_learn` — Xác suất học thêm được kiến thức mới
- `p_slip` — Xác suất làm sai dù đã hiểu bài
- `p_guess` — Xác suất đoán đúng dù chưa hiểu bài
- `p_init` — Xác suất hiểu bài từ trước khi làm

**Dữ liệu đầu vào** (Từ Silver Layer):
- `oulad_assessments` — Cấu trúc và loại bài kiểm tra
- `oulad_student_assessment` — Kết quả điểm số chi tiết của học viên

**Đầu ra Gold Iceberg**:
- Bảng: `gold_catalog.gold_db.oulad_bkt_mastery`
- Cột chính: `user_id`, `skill_name`, `correct_predictions`

---

### LightGCN - Gợi Ý Học Liệu Cá Nhân Hóa

**File**: [`data_pipeline/jobs/gold_recsys_pipeline.py`](data_pipeline/jobs/gold_recsys_pipeline.py)

**Mục đích**: Học vector nhúng (embeddings) cho học viên và tài liệu dựa trên đồ thị tương tác để đề xuất các tài liệu phù hợp nhất.

**Kiến trúc**:
- Kích thước vector nhúng: 64 (`d_dim=64`)
- Lớp đồ thị: 3 lớp Graph Convolution
- Loss function: Bayesian Personalized Ranking (BPR)
- Bộ lọc tương tác yếu: loại bỏ các tương tác dưới phân vị 50%.

**Đầu ra Gold Iceberg**:
- Bảng user embeddings: `gold_catalog.gold_db.oulad_recsys_user_embeddings`
- Bảng item embeddings: `gold_catalog.gold_db.oulad_recsys_item_embeddings`

---

## Kiến Trúc Hybrid: Offline Training và NRT Inference

Kiến trúc tách biệt giữa huấn luyện định kỳ và suy luận thời gian thực để tối ưu tài nguyên:

| Layer | Tần suất | Job thực hiện |
|-------|----------|---------------|
| **Offline Training** | 12 giờ một lần | `gold_recsys_pipeline.py`, `gold_bkt_pipeline.py`, `gold/oulad.py` |
| **NRT Inference** | 15 phút một lần | `nrt_gold_inference.py` |

**Quy trình NRT**:
1. Đọc các sự kiện tương tác mới nhất trong 15 phút qua từ Silver Layer.
2. Tải vector nhúng tĩnh từ Gold Iceberg.
3. Nhân ma trận vector nhúng (`item_matrix @ u_vec` qua NumPy) để cập nhật gợi ý (< 1ms).
4. Ghi kết quả ra `nrt_recommendations.parquet` trên Serving Layer.

---

## Hạ Tầng Cloud (Azure)

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

### Triển Khai Các Manifests Kubernetes Lên AKS

Sau khi chuẩn bị Secret (`oulad-runtime`) và đẩy Docker image lên ACR, triển khai toàn bộ các thành phần của hệ thống lên cụm AKS qua các file manifests:

1. **Triển khai Cụm Kafka KRaft (Event Broker)**:
   ```bash
   kubectl apply -f infra/manifests/kafka-kraft.yaml
   ```

2. **Triển khai Các Dịch Vụ Quản Trị & Hạ Tầng (Redis, Nessie, MLflow)**:
   ```bash
   kubectl apply -f infra/manifests/management-services.yaml
   ```

3. **Triển khai API Gateway & Serving Service (FastAPI & Models serving)**:
   ```bash
   kubectl apply -f infra/manifests/api-gateway.yaml
   kubectl apply -f infra/manifests/api-serving.yaml
   ```

4. **Triển khai Spark Structured Streaming (Xử lý Clickstream thời gian thực)**:
   ```bash
   kubectl apply -f infra/manifests/spark-streaming-job.yaml
   ```

5. **Triển khai Giao Diện Học Viên (React Frontend - LMS Simulator)**:
   ```bash
   kubectl apply -f infra/manifests/frontend-demo.yaml
   ```

6. **Triển khai Streamlit Dashboard (Cohort Analytics)**:
   ```bash
   kubectl apply -f infra/manifests/streamlit-dashboard.yaml
   ```

7. **Triển khai CronJob NRT (Inference 15 phút/lần)**:
   ```bash
   kubectl apply -f infra/manifests/oulad-nrt-cronjob.yaml
   ```

8. **Triển khai Cấu Hình Giám Sát Observability (Prometheus Rules & Grafana Operations Dashboard)**:
   ```bash
   kubectl apply -f infra/manifests/prometheus-rules-blearn-operations.yaml
   kubectl apply -f infra/manifests/grafana-dashboard-blearn-operations.yaml
   ```

---

## Cấu Hình Môi Trường và Chạy Dịch Vụ

### Biến môi trường và thông tin kết nối

Cấu hình các biến môi trường sau để chạy các dịch vụ:

```bash
# Azure Storage Credentials
export AZURE_STORAGE_ACCOUNT=stblearnminhdata2026
export AZURE_STORAGE_KEY="<your-azure-storage-key>"

# JWT Authentication
export JWT_SECRET_KEY="b-learn-super-secret-key-1015"
export CORS_ALLOW_ORIGINS="*"

# Real-time Event Streaming
export KAFKA_BOOTSTRAP_SERVERS="kafka-service.blearn-medallion.svc.cluster.local:9092"
export KAFKA_TOPIC="learning-events"
export CLICK_FALLBACK_LOG_PATH="/tmp/fallback_clicks.log"

# Spark & NRT Options
export SPARK_DRIVER_MEMORY=8g
export NRT_WINDOW_MINUTES=15
```

> [!NOTE]
> Nếu không có `AZURE_STORAGE_KEY`, các dịch vụ API Gateway và Streamlit sẽ tự động đọc dữ liệu từ Public URL của Azure Storage hoặc các file local.

---

### Hướng dẫn chạy local

#### 1. FastAPI Serving Gateway (Backend API)
Serving Gateway quản lý xác thực JWT, nhận clickstream, thực hiện Bayesian BKT và live inference LightGBM thời gian thực.

```bash
source .venv/bin/activate
pip install -r data_pipeline/requirements.txt

# Khởi chạy Serving Gateway
uvicorn backend-api.serving_gateway:app --host 0.0.0.0 --port 8000 --reload
```
API hoạt động tại `http://localhost:8000`. Xem tài liệu Swagger API tại `/docs`.

#### 2. React Frontend Demo
Giao diện giả lập LMS và luồng adaptive learning.

```bash
cd frontend-demo
echo "VITE_GATEWAY_URL=http://localhost:8000" > .env
npm install
npm run dev
```
Giao diện chạy tại `http://localhost:5173`.

#### 3. Streamlit Dashboard (Cohort Analytics UI)
Dashboard thống kê tổng quan khóa học và chi tiết học viên.

```bash
streamlit run dashboard/app.py
```
Streamlit chạy tại `http://localhost:8501`.

---

### Thiết lập trên macOS

Xem hướng dẫn chi tiết tại [`docs/guide-macos.md`](docs/guide-macos.md).

```bash
brew install openjdk@17

python3 -m venv .venv
source .venv/bin/activate
pip install -r data_pipeline/requirements.txt

az aks get-credentials --resource-group RG-BLEarn-Compute --name aks-blearn-dev
```

---

## Thư viện Python

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

> [!NOTE]
> Apache Iceberg runtime được nạp qua Maven (`spark.jars.packages`) khi chạy Spark.

---

## Quy Trình Chạy Pipeline

### Tầng Bronze (Ingestion)

```bash
# Compact EdNet CSVs thành Parquet groups (chỉ cần chạy một lần)
make bronze-consolidate-ednet

# Tạo manifest JSON
make bronze-full-manifest

# Nạp dữ liệu vào Iceberg (ADLS Gen2)
SPARK_DRIVER_MEMORY=8g AZURE_STORAGE_KEY="<key>" make bronze-full-ingest

# Kiểm tra số dòng nguồn và đích
make bronze-full-verify

# Kiểm tra metadata columns
make bronze-full-audit

# Chạy toàn bộ Bronze flow
SPARK_DRIVER_MEMORY=8g AZURE_STORAGE_KEY="<key>" make bronze-full-flow
```

**Output**: `abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/full/`

---

### Tầng Silver (Transform & Anonymize)

```bash
AZURE_STORAGE_KEY="<key>" make silver-run
```

**Thao tác thực hiện**:
- Đọc từ `bronze_catalog.full_db.*`
- Băm `id_student` → `student_id_hash` bằng SHA-256
- Chuẩn hóa kiểu dữ liệu, loại bỏ bản ghi NULL
- Ghi vào `silver_catalog.silver_db.*` trên ADLS Gen2

**Output**: `abfss://silver@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/silver/`

---

### Tầng Gold (Feature Engineering & Models)

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

## NRT Inference (Near-Real-Time)

```bash
# Chạy thủ công cục bộ
AZURE_STORAGE_KEY="<key>" make nrt-inference-run

# Deploy CronJob NRT lên AKS (mỗi 15 phút)
make k8s-deploy-nrt

# Trigger NRT ngay lập tức
make k8s-nrt-trigger-once
```

**Luồng hoạt động**:
```
NRT Job (mỗi 15 phút)
  ├─ Load frozen embeddings từ Gold Iceberg
  ├─ Scan Silver: có sự kiện mới trong 15 phút qua?
  │   ├─ Không có → Thoát sớm (Exiting early)
  │   └─ Có → Chạy NumPy dot-product cho các sinh viên hoạt động
  └─ Ghi nrt_recommendations.parquet lên Serving Layer
```

---

## Hệ Thống Chịu Lỗi & Dự Phòng (Failover)

Kiến trúc Active-Passive: Airflow là Primary, K8s Native CronJobs là Passive.

### Kích Bản Airflow Lỗi → Kích Hoạt Failover

```bash
# Kích hoạt lịch K8s thay thế Airflow
make k8s-activate-failover-schedule

# Kết quả: 3 CronJobs được kích hoạt:
#   • oulad-bronze-cronjob     → 02:00 UTC hàng ngày
#   • oulad-silver-gold-cronjob → 03:00 UTC hàng ngày
#   • oulad-nrt-cronjob        → mỗi 15 phút

# Kiểm tra trạng thái
make k8s-failover-status
```

### Khi Airflow Phục Hồi → Tắt Failover

```bash
# Tắt Bronze + Silver-Gold CronJobs (giữ NRT)
make k8s-deactivate-failover-schedule
```

---

## Airflow High Availability (HA)

Cấu hình nâng cấp Airflow từ `LocalExecutor` lên `KubernetesExecutor` với 2 Schedulers:

**File**: [`infra/airflow-values.yaml`](infra/airflow-values.yaml)

```bash
make airflow-upgrade-ha

# Kiểm tra schedulers
kubectl get pods -n blearn-medallion -l component=scheduler
```

| Thuộc tính | Trước | Sau |
|-----------|-------|-----|
| Executor | `LocalExecutor` | `KubernetesExecutor` |
| Schedulers | 1 replica | **2 replicas (Active-Active HA)** |
| Task isolation | Process-level | **Pod-level (K8s Pod per Task)** |

---

## Airflow DAG

**File**: [`data_pipeline/dags/oulad_medallion_dag.py`](data_pipeline/dags/oulad_medallion_dag.py)

DAG `oulad_medallion_pipeline` (on-demand, `schedule=None`):

```
bronze_ingest → silver_transform → gold_feature_model
```

Mỗi Task chạy trong Pod K8s riêng biệt (`KubernetesPodOperator`). Credentials được inject từ K8s Secret `oulad-runtime`.

**Triển khai DAG**:
```bash
kubectl create configmap oulad-medallion-dag \
  --from-file=data_pipeline/dags/oulad_medallion_dag.py \
  -n blearn-medallion
```

---

## Dashboard Streamlit

**File**: [`dashboard/app.py`](dashboard/app.py)

### Cấu Trúc 3 Phân Hệ (Tabs)

| Phân hệ (Tab) | Mô tả | Chi tiết kỹ thuật |
|---|---|---|
| **Tab 1: Tổng Quan (Cohort Analytics)** | Quản lý tổng quan học tập của toàn bộ khóa học | - KPI Cards: Tổng số học viên, tỷ lệ rủi ro trung bình, kỹ năng gây kẹt nhất.<br>- Plotly Pie Chart: Phân phối giới tính.<br>- Plotly Bar Chart: Trình độ học vấn & Top 8 vùng miền.<br>- Plotly Line Chart: Xu hướng tương tác học viên theo tuần. |
| **Tab 2: Hồ Sơ Cá Nhân (Student Deep-Dive)** | Chi tiết rủi ro và trạng thái học tập của từng học viên | - Cảnh báo rủi ro bỏ học (LightGBM).<br>- Trạng thái thành thạo kỹ năng (pyBKT).<br>- Đề xuất top 5 tài liệu học tập phù hợp (LightGCN). |
| **Tab 3: Giả Lập LMS (External App Integration)** | Mô phỏng tương tác của học viên trên LMS | - Cho phép mô phỏng học tài liệu đề xuất.<br>- Cập nhật vector nhúng thời gian thực: $u_{new} = u_{old} + 0.3 \cdot i_{clicked}$.<br>- Tính toán lại gợi ý trực tiếp (Real-time Adaptive Learning).<br>- Hiển thị log xử lý của luồng. |

### Design System & Performance

- **Font & Theme**: Google Fonts Outfit + Glassmorphism dark theme.
- **Trực quan hóa**: Sử dụng Plotly Express cho đồ thị tương tác.
- **Hiệu suất**: Đọc trực tiếp các tệp Parquet từ Azure ADLS Gen2 bằng `@st.cache_data`. Gợi ý dot-product chạy qua NumPy trên CPU với độ trễ < 1ms.

---

## Các Lệnh Makefile

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
make silver-run                  # OULAD Bronze → Silver
make gold-lgbm-run               # Chạy LightGBM risk model
make gold-bkt-run                # Chạy pyBKT knowledge tracing model
make gold-recsys-run             # Chạy LightGCN recommendation model
make serving-export-run          # Xuất Gold → Parquet Serving Layer
make streamlit-local-run         # Khởi động Streamlit dashboard locally
```

### NRT (Near-Real-Time)

```bash
make nrt-inference-run           # Chạy NRT inference thủ công
make k8s-deploy-nrt              # Deploy CronJob NRT lên AKS (*/15 * * * *)
make k8s-nrt-trigger-once        # Trigger NRT job ngay lập tức trên AKS
```

### Kubernetes (AKS)

```bash
make k8s-test-bkt                # Kích hoạt test BKT job trên AKS
make k8s-serving-export          # Trigger Serving Export job trên AKS
make k8s-deploy-streamlit        # Deploy Streamlit dashboard lên AKS
make k8s-streamlit-status        # Xem IP LoadBalancer của Streamlit
make k8s-clean-test              # Xóa các Job tạm thời
```

### Failover & HA

```bash
make k8s-activate-failover-schedule    # Kích hoạt K8s CronJobs khi Airflow lỗi
make k8s-deactivate-failover-schedule  # Tắt K8s CronJobs khi Airflow hoạt động lại
make k8s-failover-status               # Kiểm tra trạng thái CronJobs
make airflow-upgrade-ha                # Nâng cấp Airflow HA
```

---

## K8s Manifests Chi Tiết

### NRT CronJob (`oulad-nrt-cronjob.yaml`)

```yaml
schedule: "*/15 * * * *"
concurrencyPolicy: Forbid      # Bỏ qua nếu job cũ chưa chạy xong
backoffLimit: 0                # Không retry
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
```

### Streamlit Deployment (`streamlit-dashboard.yaml`)

```yaml
command: ["streamlit", "run", "/app/dashboard/app.py",
          "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Kết Quả Kiểm Thử End-to-End (E2E)

Các giai đoạn kiểm thử đã được thực thi trên cụm AKS:

| Giai đoạn | Nội dung | Kết quả |
|-----------|----------|---------|
| **G1** — Xác thực Image | Restart Streamlit + Deploy NRT CronJob | Pod Rolling update thành công |
| **G2** — Batch Serving Export | Trigger `oulad-serving-export-job` | Hoàn thành trong 75 giây, 4 file Parquet ghi thành công |
| **G3** — NRT Inference | Trigger `nrt-manual-xxx` job | Load 25,166 users / 6,268 items embeddings, thoát sớm khi không có event mới |
| **G4** — Dashboard Live | Kiểm tra http://135.171.193.190 | IP Public khớp, UI hoạt động đúng |
| **G5** — Failover | `make k8s-activate-failover-schedule` | 3 CronJobs hoạt động ở trạng thái sẵn sàng gánh tải |

---

## Sửa Lỗi Thường Gặp (Troubleshooting)

### Lỗi Platform Mismatch (Apple Silicon → AKS)

```
Error: no match for platform in manifest: not found
```

**Nguyên nhân**: Docker build trên Mac M-series tạo image `linux/arm64` trong khi AKS yêu cầu `linux/amd64`.

**Giải pháp**:
```bash
docker build --platform linux/amd64 \
  -t acrblearnminh2026.azurecr.io/oulad-medallion:latest .
docker push acrblearnminh2026.azurecr.io/oulad-medallion:latest
kubectl rollout restart deployment/blearn-streamlit-ui -n blearn-medallion
```

### Lỗi Dashboard Crash: `File does not exist: dashboard/app.py`

**Nguyên nhân**: Dockerfile chưa copy thư mục `dashboard/`.

**Giải pháp**: Cập nhật Dockerfile:
```dockerfile
COPY dashboard/ /app/dashboard/
```

### AKS Pod OOMKilled (Out of Memory)

**Nguyên nhân**: Cấp phát CPU/RAM chưa đủ cho Spark.

**Giải pháp**: Tăng tài nguyên cấu hình trong yaml:
```yaml
resources:
  requests:
    cpu: "800m"
  limits:
    cpu: "1.5"
```

---

## Tài Liệu Bổ Sung

- [Medallion Architecture](docs/medallion_architecture.md) — Chi tiết thiết kế luồng Bronze, Silver, Gold và hạ tầng
- [BKT Pipeline Report](docs/bkt_pipeline_report.md) — Phân tích hiệu năng mô hình pyBKT và tối ưu hóa
- [macOS Setup Guide](docs/guide-macos.md) — Hướng dẫn thiết lập môi trường chạy local trên macOS

---

## Dữ Liệu Nguồn

| Dataset | Nội dung | Kích thước ước tính |
|---------|----------|---------------------|
| **EdNet** (KT1/KT2/KT4) | Tương tác bài tập của học viên | ~4M sự kiện |
| **OULAD** | Dữ liệu học tập mở của Đại học Mở (UK) | ~32K học viên |
| **SED** | Dữ liệu giáo dục bổ sung | — |
| **Content** | Siêu dữ liệu bài giảng và tài nguyên | — |

---

## Thông Tin Hệ Thống Live

| Thành phần | Địa chỉ / Tên |
|-----------|---------------|
| Streamlit Dashboard | http://135.171.193.190 |
| Azure Storage Account | `stblearnminhdata2026` |
| Azure Container Registry | `acrblearnminh2026.azurecr.io` |
| AKS Cluster | `aks-blearn-dev` (Southeast Asia) |
| K8s Namespace | `blearn-medallion` |
| GitHub Repository | https://github.com/minhtran1015/b-learn |

---

*Hệ thống được thiết kế và triển khai áp dụng các nguyên tắc DataOps và MLOps.*
# Dac Ta Chi Tiet Kien Truc Ky Thuat

Tai lieu nay tong hop dac ta cong nghe cot loi cua he thong B-Learn theo 3 lop: Data Platform, Multi-Model AI Core va Serving & MLOps Gate.

## 1. Tong quan kien truc

He thong van hanh theo chuoi:
- Thu thap su kien hoc tap thoi gian thuc vao Kafka topic `learning-events`.
- Spark Structured Streaming xu ly micro-batch va ghi vao Iceberg tren ADLS Gen2.
- Cac pipeline Gold cap nhat du bao rui ro, do thanh thuc, va goi y hoc lieu.
- FastAPI Serving Gateway phuc vu frontend-demo va dashboard thong qua JWT + cache bo nho.
- Streamlit Dashboard giam sat SLA, drift va suc khoe MLOps.

## 2. Big Data Ingestion Pipeline

## 2.1 Kafka KRaft mode (ZooKeeper-less)

- Cum Kafka duoc cau hinh KRaft mode voi 1 StatefulSet.
- Bien moi truong quan trong:
- `KAFKA_PROCESS_ROLES=broker,controller`
- `KAFKA_CONTROLLER_QUORUM_VOTERS=1@127.0.0.1:9093`
- Kien truc nay bo thanh phan ZooKeeper, giam footprint RAM va don gian van hanh cho moi truong demo/hoc thuat.

## 2.2 Spark Structured Streaming micro-batch 10 giay

- Job streaming doc tu Kafka topic `learning-events`.
- Co che chong mat du lieu khi he thong dao trang thai:
- `.option("failOnDataLoss", "false")`
- Chu ky xu ly:
- `.trigger(processingTime="10 seconds")`
- Cua so su kien:
- Watermark 10 phut de xu ly out-of-order events.
- Session window 30 phut de gom nhom hanh vi hoc tap.

## 2.3 Hang rao ban tin loi (poison message guardrail)

- JSON parser chay che do:
- `mode='PERMISSIVE'`
- Cot luu payload loi:
- `_corrupt_record`
- Ban ghi co `_corrupt_record` khong null bi loai truoc khi ghi Iceberg.
- Muc tieu: giu stream on-drift, khong dung toan bo pipeline vi mot message xau.

## 2.4 Luu tru Iceberg tren ADLS Gen2

- Bronze/Silver/Gold catalog duoc to chuc dang bang Iceberg phan tan.
- Warehouse dat tren ADLS Gen2 (`abfss://...dfs.core.windows.net/iceberg_warehouse/...`).
- Loi ich ky thuat:
- Metadata table-level ro rang, ho tro schema evolution.
- Doc/ghi theo partition va checkpoint streaming co tinh nhat quan cao.
- Phu hop mo hinh Medallion de tach nghiep vu ingestion, transform, serving export.

## 3. Multi-Model AI Serving Core

## 3.1 Mo hinh 1 - pyBKT

- Vai tro: uoc luong do thanh thuc kien thuc theo ky nang/chuong hoc.
- Dau ra duoc tong hop vao bo chi so hoc tap phuc vu phan tich nang luc.
- Trong dashboard, chi so pyBKT duoc kiem soat SLA qua ROC-AUC.

## 3.2 Mo hinh 2 - LightGBM (Dropout Risk)

- Vai tro: du bao xac suat bo hoc tu chuoi hanh vi clickstream va dac trung hoc tap.
- Dau ra chinh: `dropout_probability` tren moi hoc vien.
- Gia tri nay duoc frontend quy doi thanh ty le do:
- `pass_rate = (1 - dropout_probability) * 100`.

## 3.3 Mo hinh 3 - LightGCN (RecSys)

- Vai tro: hoc embedding user-item tren do thi tuong tac hoc tap.
- Tai serving gateway, xep hang goi y theo Dot-Product:
- `scores = np.dot(i_embs, u_emb)`
- Top-N hoc lieu co score cao nhat duoc tra ve de ca nhan hoa lo trinh hoc.

## 4. Serving & MLOps Gate

## 4.1 FastAPI high-speed serving

- API framework: FastAPI.
- Bao mat va phan quyen:
- JWT (`/login` cap `access_token`, `Bearer` auth cho cac endpoint nghiep vu).
- Xu ly bat dong bo:
- `BackgroundTasks` duoc dung de day click/submission vao Kafka ma khong chan UI.

## 4.2 Bo dem RAM va Closed-Loop risk shift

- Bo nho tam `_assessment_shifts` luu bien dong rui ro theo `student_id_hash`.
- Khi hoc vien nop bai (`/submit-assessment`):
- Score >= 50%: giam rui ro (reduction +0.05, tuc dropout probability giam).
- Score < 50%: tang rui ro (reduction -0.10, tuc dropout probability tang).
- Cap nhat duoc ap dung ngay tren cache `df_risk`, tao hieu ung dong tren AnalyticsPage truoc khi dong bo day du ve lakehouse.
- Co endpoint `/reset-assessment-shifts` de dua he thong ve baseline cho lan demo tiep theo.

## 4.3 Control gate SLA Drift tren Streamlit Dashboard

- Dashboard co tab Infrastructure/MLOps de theo doi:
- Live Grafana iframe (telemetry runtime).
- Bang Data Quality Guardrails (null rate, schema conformance, drift PSI, HTTP 5xx).
- Nguong SLA duoc dinh nghia cho 3 mo hinh:
- LightGBM PR-AUC.
- pyBKT ROC-AUC.
- LightGCN Recall@10.
- Khi metric thap hon nguong, dashboard phat canh bao va yeu cau retraining.

## 5. Interface contracts (tom tat endpoint)

- `POST /login`: cap JWT token.
- `POST /track-click`: nhan clickstream, day Kafka bang task nen.
- `GET /recommendations/{student_id_hash}`: tra recsys + dropout probability.
- `POST /submit-assessment`: cap nhat closed-loop risk shift va phat su kien `assessment_submission`.
- `POST /reset-assessment-shifts`: reset trang thai demo.
- `GET /health`: kiem tra suc khoe API.

## 6. Gia tri ky thuat cho hoi dong cham diem

- Tinh khang loi: co guardrail cho offset Kafka va poison message.
- Tinh thoi gian thuc: micro-batch 10 giay + cap nhat dong ngay tai Serving cache.
- Tinh mo rong: Medallion + Iceberg + ADLS Gen2 de phuc vu du lieu lon.
- Tinh van hanh: GreenOps suspend/resume giam chi phi cloud nhung van bao toan quy trinh demo.

## 7. Frontend, Gateway, va Serving Contracts

### Frontend-demo architecture that

- `frontend-demo/src/main.jsx` mount app vao `BrowserRouter` va `AuthProvider`.
- `frontend-demo/src/App.jsx` dinh nghia route tree cho login, register, courses, materials, assignments, analytics, discussions, calendar, messages, help, settings, profile.
- `frontend-demo/src/api/gateway.js` la lop client ket noi Gateway va quan ly token/session trong browser.
- `frontend-demo/src/auth/AuthContext.jsx` luu user demo local, hash password bang Web Crypto, va goi Gateway sau khi login/register.

### LocalStorage keys that phai biet

- `blearn.gatewayToken`: JWT bearer token.
- `blearn.studentHash`: student_id_hash da xac dinh.
- `blearn.recommendationMaterials`: cache tai lieu goi y.
- `blearn.tempUsers`: danh sach user demo.
- `blearn.currentUserId`: session user hien tai.
- `blearn.submitted_assignments`: cac assignment da nop.

### Hai server surface khac nhau trong repo

- `backend-api/serving_gateway.py`: serving gateway co JWT, click tracking, recommendation, submit-assessment, reset-assessment-shifts.
- `dashboard/api_server.py`: serving API doc du lieu Gold trong RAM, nhe I/O, phuc vu trang Web/REST giu do trễ thap.

### Su khac nhau ve muc dich

- Gateway job: dong, co in-memory risk shift, dat trung tam cho demo closed-loop.
- Dashboard api_server: doc du lieu da nap san vao RAM, phuc vu chart va API tra loi nhanh.

## 8. Deployment Matrix and Exact Ports

| K8s object | Command / image | Port | Purpose |
|---|---|---:|---|
| `blearn-frontend-demo` | `acrblearnminh2026.azurecr.io/oulad-frontend:latest` | 80 | Giao dien hoc vien |
| `blearn-api-gateway` | `python backend-api/serving_gateway.py` | 8000 | JWT + click + recommendation + assessment |
| `blearn-api-serving` | `uvicorn dashboard.api_server:app --host 0.0.0.0 --port 8000` | 8000 | REST phuc vu Gold data |
| `blearn-streamlit-ui` | `streamlit run /app/dashboard/app.py` | 8501 | Dashboard giang vien |
| `spark-streaming-job` | `python -m data_pipeline.jobs.stream_clickstream` | n/a | Streaming pipeline |
| `kafka-stream` | `apache/kafka:3.7.0` | 9092/9093 | Kafka KRaft broker/controller |

### Resource envelopes

- Frontend demo: 100m CPU / 128Mi request, 250m CPU / 256Mi limit.
- API Gateway: 100m CPU / 256Mi request, 250m CPU / 512Mi limit.
- API Serving: 200m CPU / 512Mi request, 500m CPU / 1Gi limit.
- Streamlit: 200m CPU / 512Mi request, 500m CPU / 1Gi limit.
- Spark streaming: 200m CPU / 512Mi request, 500m CPU / 1Gi limit.
- Kafka: 250m CPU / 512Mi request, 500m CPU / 1Gi limit.

## 9. Data Products and File Contracts

### Serving layer files

- `risk_predictions.parquet`: dropout probability, predicted class, student mapping.
- `bkt_mastery.parquet`: knowledge mastery outputs from pyBKT.
- `user_embeddings.parquet`: LightGCN user vectors.
- `item_embeddings.parquet`: LightGCN item vectors.
- `cohort_stats.parquet`: demographic and engagement aggregates for dashboard charts.
- `lms_simulator.parquet`: metadata for material titles, types, chapter, duration.
- `system_metrics.parquet`: SLA, freshness, resource, and MLOps KPIs.
- `nrt_recommendations.parquet`: refreshed near-real-time recommendation slice.

### Producer/consumer map

- `export_to_serving.py` writes all base serving files.
- `dashboard/api_server.py` reads all base serving files into process RAM at startup.
- `dashboard/app.py` reads the serving files and shows charts, tables, and SLA drift.
- `frontend-demo` uses the Gateway to fetch recommendations and submit assessment events.

### Why the flat serving layer exists

- The UI needs fast startup and low-latency reads.
- Parquet flat files avoid querying Iceberg during every browser refresh.
- RAM cache in `dashboard/api_server.py` removes repeated network I/O for each API request.

## 10. Full End-to-End Dataflow

1. User action happens in `frontend-demo`.
2. Click events go to `/track-click` and land in Kafka topic `learning-events`.
3. `stream_clickstream.py` consumes Kafka, sessionizes clicks, and writes Bronze Iceberg `oulad_studentvle`.
4. `silver/oulad.py` cleans Bronze tables, hashes student IDs, and writes Silver Iceberg tables.
5. `gold/oulad.py` builds features, trains LightGBM, and writes Gold risk tables plus model artifact.
6. `gold_bkt_pipeline.py` trains pyBKT and writes mastery outputs.
7. `gold_recsys_pipeline.py` trains LightGCN and writes user/item embeddings.
8. `export_to_serving.py` flattens Gold tables to the serving container.
9. `dashboard/api_server.py` and `backend-api/serving_gateway.py` consume serving files.
10. `dashboard/app.py` visualizes metrics, Grafana iframe, and SLA drift.

## 11. Model-Specific Details That Matter Operationally

### LightGBM risk model

- Feature engineering uses OULAD cut-off day 30 and aggregates VLE/assessment behavior.
- Target classes are normalized to Withdrawn, Fail, and Success.
- Artifacts are uploaded as joblib + JSON metrics to the gold container.

### pyBKT mastery model

- Uses `skill_name = code_module + '_' + assessment_type`.
- Excludes `Exam` rows from sequential training.
- Trains on course chunks and evaluates ROC-AUC per course.

### LightGCN recommender

- Builds a normalized sparse adjacency matrix from user-item click pairs.
- Trains 10 epochs on CPU with BPR loss.
- Outputs recall@10 and ndcg@10 metrics for MLOps reporting.

### NRT inference

- Does not retrain models.
- Reuses frozen embeddings from Gold.
- Refreshes only recent interaction-driven recommendations in 15-minute windows.

## 12. Repo Surfaces That Are Supporting, Not Primary

- `backend-api/` contains the decoupled API serving gateway server.
- `data_pipeline/jobs/ednet.py` and `data_pipeline/jobs/sed.py` only carry dataset-specific defaults/helpers.
- `data_pipeline/README.md` documents the older Bronze-first, Medallion-oriented execution path and the EdNet consolidation story.
- `infra/manifests/oulad-bronze-cronjob.yaml`, `oulad-silver-cronjob.yaml`, and `oulad-nrt-cronjob.yaml` are failover or scheduled execution paths around the core pipeline.

## 13. Operating Assumptions for Reviewers

- Closed-loop learning demo depends on the API Gateway being reachable on port 8000.
- Kafka streaming depends on the topic `learning-events` being present.
- Dashboard drift checks depend on `system_metrics.parquet` being refreshed by the serving export job.
- The frontend can still show useful fallback data if Gateway/Serving is temporarily degraded.
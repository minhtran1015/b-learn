ROOT := $(CURDIR)
PYTHON ?= $(ROOT)/.venv/bin/python
TERRAFORM ?= terraform
SPARK_DRIVER_MEMORY ?= 8g
AZURE_STORAGE_ACCOUNT ?= stblearnminhdata2026
AZURE_STORAGE_KEY ?=
FULL_SOURCE_ROOT ?= large-data
FULL_CONSOLIDATED_ROOT ?= infra/staging/ednet_consolidated_full_compacted
FULL_MANIFEST_PATH ?= full_data_manifest.json
FULL_OUTPUT_ROOT ?= abfss://bronze@$(AZURE_STORAGE_ACCOUNT).dfs.core.windows.net/iceberg_warehouse/full/
FULL_NAMESPACE ?= full
SILVER_OUTPUT_ROOT ?= abfss://silver@$(AZURE_STORAGE_ACCOUNT).dfs.core.windows.net/iceberg_warehouse/silver/
GOLD_OUTPUT_ROOT ?= abfss://gold@$(AZURE_STORAGE_ACCOUNT).dfs.core.windows.net/iceberg_warehouse/gold/
INFRA_DIR ?= infra

export SPARK_DRIVER_MEMORY
export AZURE_STORAGE_ACCOUNT
export AZURE_STORAGE_KEY

.PHONY: help bronze-discover-full bronze-consolidate-ednet bronze-full-manifest bronze-full-ingest bronze-full-verify bronze-full-audit bronze-full-flow silver-oulad-transform gold-oulad-train gold-bkt-run medallion-oulad-flow infra-terraform-init infra-terraform-plan infra-terraform-apply nrt-inference-run k8s-deploy-nrt k8s-nrt-trigger-once k8s-activate-failover-schedule k8s-deactivate-failover-schedule k8s-failover-status airflow-upgrade-ha api-local-run k8s-deploy-api k8s-api-status react-local-install react-local-run react-local-build

help:
	@printf '%s\n' \
		'Bronze flow targets:' \
		'  make bronze-consolidate-ednet   # compact EdNet CSVs into parquet groups' \
		'  make bronze-full-manifest       # build full_data_manifest.json' \
		'  make bronze-full-ingest         # load full manifest into Iceberg full_db' \
		'  make bronze-full-verify         # cross-check source vs. Bronze counts' \
		'  make bronze-full-audit          # sample audit metadata columns' \
		'  make bronze-full-flow           # run consolidate -> ingest -> verify -> audit' \
		'Silver/Gold flow targets:' \
		'  make silver-oulad-transform     # clean OULAD Bronze into Silver Iceberg tables' \
		'  make gold-oulad-train           # build Gold features, train LGBM, write scores' \
		'  make medallion-oulad-flow       # run Silver then Gold'

bronze-discover-full:
	$(PYTHON) -m data_pipeline.ingestion.ingest \
		--source-root $(FULL_SOURCE_ROOT) \
		--manifest-path $(FULL_MANIFEST_PATH) \
		discover

bronze-consolidate-ednet:
	$(PYTHON) -m data_pipeline.ingestion.ingest consolidate-ednet \
		--ednet-source-root $(FULL_SOURCE_ROOT)/EdNet \
		--consolidated-root $(FULL_CONSOLIDATED_ROOT) \
		--target-partitions 10 \
		--batch-size 250

bronze-full-manifest:
	$(PYTHON) - <<'PY'
	from pathlib import Path

	from data_pipeline.utils.manifest import ManifestRecord, discover_files, write_manifest

	repo_root = Path("$(ROOT)")
	source_root = repo_root / "$(FULL_SOURCE_ROOT)"
	manifest_path = repo_root / "$(FULL_MANIFEST_PATH)"
	consolidated_root = repo_root / "$(FULL_CONSOLIDATED_ROOT)"

	records = [record for record in discover_files(source_root) if record.dataset != "ednet"]
	for group in ("kt1", "kt2", "kt4"):
	    records.append(
	        ManifestRecord(
	            source_path=str((consolidated_root / group).resolve()),
	            dataset="ednet",
	            table=f"ednet_{group}_events",
	            file_type="parquet",
	            partition_hint="_ingest_date",
	            ingest_strategy="parquet",
	        )
	    )

	write_manifest(records, manifest_path)
	print(f"Wrote {len(records)} records to {manifest_path}")
	PY

bronze-full-ingest: bronze-full-manifest
	$(PYTHON) -m data_pipeline.ingestion.ingest \
		--source-root $(FULL_SOURCE_ROOT) \
		--manifest-path $(FULL_MANIFEST_PATH) \
		--output-root "$(FULL_OUTPUT_ROOT)" \
		ingest \
		--namespace $(FULL_NAMESPACE)

bronze-full-verify:
	$(PYTHON) -m data_pipeline.ingestion.ingest \
		--manifest-path $(FULL_MANIFEST_PATH) \
		--output-root "$(FULL_OUTPUT_ROOT)" \
		verify

bronze-full-audit:
	$(PYTHON) - <<'PY'
	from data_pipeline.ingestion.ingest import build_spark

	spark = build_spark("B-Learn_Bronze_Metadata_Check", "$(FULL_OUTPUT_ROOT)")
	try:
	    for table in [
	        "bronze_catalog.full_db.ednet_kt1_events",
	        "bronze_catalog.full_db.oulad_studentinfo",
	    ]:
	        print(f"== {table} ==")
	        spark.sql(
	            f"SELECT _ingest_at, _source_file, _source_dataset FROM {table} LIMIT 5"
	        ).show(truncate=False)
	finally:
	    spark.stop()
	PY

bronze-full-flow: bronze-consolidate-ednet bronze-full-ingest bronze-full-verify bronze-full-audit

silver-oulad-transform:
	$(PYTHON) -m data_pipeline.silver.oulad \
		--input-catalog bronze_catalog \
		--input-namespace full_db \
		--output-catalog silver_catalog \
		--output-namespace silver \
		--output-root "$(SILVER_OUTPUT_ROOT)"

gold-oulad-train:
	$(PYTHON) -m data_pipeline.gold.oulad \
		--input-catalog silver_catalog \
		--input-namespace silver_db \
		--output-catalog gold_catalog \
		--output-namespace gold \
		--output-root "$(GOLD_OUTPUT_ROOT)"

medallion-oulad-flow: silver-oulad-transform gold-oulad-train

infra-terraform-init:
	cd $(INFRA_DIR) && $(TERRAFORM) init

infra-terraform-plan:
	cd $(INFRA_DIR) && $(TERRAFORM) plan

infra-terraform-apply:
	cd $(INFRA_DIR) && $(TERRAFORM) apply

# --- AIRFLOW MANAGEMENT ---

# 1. Deploy/upgrade Airflow on AKS cluster using Helm
airflow-deploy:
	helm repo add apache-airflow https://airflow.apache.org/
	helm repo update
	helm upgrade --install airflow apache-airflow/airflow \
		--namespace blearn-medallion \
		--create-namespace \
		-f infra/airflow-values.yaml

# 2. Hibernate Airflow: scale replicas to 0 to save Azure student credits
airflow-stop:
	kubectl scale deployment/airflow-webserver --replicas=0 -n blearn-medallion
	kubectl scale deployment/airflow-scheduler --replicas=0 -n blearn-medallion
	@echo "Airflow scaled to 0. No CPU/RAM consumed in AKS."

# 3. Wake up Airflow: scale replicas back to 1
airflow-start:
	kubectl scale deployment/airflow-webserver --replicas=1 -n blearn-medallion
	kubectl scale deployment/airflow-scheduler --replicas=1 -n blearn-medallion

# 4. Uninstall Airflow from AKS
airflow-destroy:
	helm uninstall airflow -n blearn-medallion

# ====================================================================
# 🌐 AZURE INFRASTRUCTURE CONTROLS (QUẢN LÝ HẠ TẦNG CHUYÊN NGHIỆP)
# ====================================================================

# Bật nhanh cụm AKS để làm việc
aks-start:
	az aks start --name aks-blearn-dev --resource-group RG-BLEarn-Compute

# Tắt cụm AKS ngay lập tức sau khi xong việc để đóng băng chi phí
aks-stop:
	az aks stop --name aks-blearn-dev --resource-group RG-BLEarn-Compute

# Kiểm tra nhanh trạng thái tất cả các Pod đang chạy trên namespace
k8s-status:
	kubectl get jobs,pods -n blearn-medallion

# ====================================================================
# ⚡ LOCAL / DEV PIPELINE EXECUTIONS (CHẠY TEST ĐỘC LẬP TỪNG TẦNG)
# ====================================================================

# 1. Chạy tầng Bronze: Nạp dữ liệu thô OULAD lên Cloud Iceberg
bronze-run:
	python -m data_pipeline.ingestion.ingest --manifest-path full_data_manifest.json --output-root abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/full/ ingest --namespace full

# 2. Chạy tầng Silver: Xử lý làm sạch, băm bảo mật SHA256 dữ liệu
silver-run:
	python -m data_pipeline.jobs.silver_transform

# 3. Chạy tầng Gold - Phân hệ Mô hình Rủi ro (LightGBM)
gold-lgbm-run:
	python -m data_pipeline.jobs.gold_transform_and_train

# 4. Chạy tầng Gold - Phân hệ Đo lường Kiến thức (pyBKT tuần tự)
gold-bkt-run:
	python -m data_pipeline.jobs.gold_bkt_pipeline

# 5. Chạy tầng Gold - Phân hệ Hệ gợi ý Tài liệu (LightGCN PyTorch)
gold-recsys-run:
	python -m data_pipeline.jobs.gold_recsys_pipeline

# 6. Chạy tầng Gold -> Serving Layer: Xuất Parquet phẳng
serving-export-run:
	python -m data_pipeline.jobs.export_to_serving

# Chạy Dashboard Streamlit cục bộ
streamlit-local-run:
	streamlit run dashboard/app.py

# Chạy Serving API FastAPI cục bộ
api-local-run:
	uvicorn dashboard.api_server:app --reload

# Cài đặt thư viện cho React Frontend Dashboard
react-local-install:
	cd frontend-dashboard && npm install

# Chạy React Frontend Dashboard cục bộ (Development)
react-local-run:
	cd frontend-dashboard && npm run dev

# Biên dịch React Frontend Dashboard cho production
react-local-build:
	cd frontend-dashboard && npm run build

# Triển khai FastAPI API Serving lên AKS
k8s-deploy-api:
	kubectl apply -f infra/manifests/api-serving.yaml

# Theo dõi IP LoadBalancer của API Serving
k8s-api-status:
	kubectl get svc blearn-api-service -n blearn-medallion


# ====================================================================
# 🔄 KUBERNETES ONE-SHOT TEST JOBS (KÍCH HOẠT CHẠY TRÊN AKS)
# ====================================================================

# Kích hoạt test job BKT trên cụm Cloud
k8s-test-bkt:
	kubectl delete job oulad-gold-bkt-test -n blearn-medallion --ignore-not-found=true
	kubectl apply -f infra/manifests/oulad-bkt-test.yaml
	@echo "Chờ 5s để Pod khởi tạo rồi theo dõi log..."
	sleep 5
	kubectl logs -f $$(kubectl get pods -n blearn-medallion -l job-name=oulad-gold-bkt-test -o jsonpath='{.items[0].metadata.name}') -n blearn-medallion

# Kích hoạt serving export job trên cụm Cloud
k8s-serving-export:
	kubectl delete job oulad-serving-export-job -n blearn-medallion --ignore-not-found=true
	kubectl apply -f infra/manifests/oulad-serving-export-job.yaml
	@echo "Chờ 5s để Pod khởi tạo rồi theo dõi log..."
	sleep 5
	kubectl logs -f job/oulad-serving-export-job -n blearn-medallion

# Triển khai Streamlit Dashboard lên AKS
k8s-deploy-streamlit:
	kubectl apply -f infra/manifests/streamlit-dashboard.yaml

# Theo dõi IP LoadBalancer của Streamlit
k8s-streamlit-status:
	kubectl get svc blearn-streamlit-service -n blearn-medallion

# Xóa toàn bộ các job test tạm thời để làm sạch cụm
k8s-clean-test:
	kubectl delete jobs --all -n blearn-medallion

# ====================================================================
# 🚀 END-TO-END AUTOMATION FLOW (LUỒNG CHẠY LIÊN HOÀN TOÀN DIỆN)
# ====================================================================

# Chạy toàn bộ chu trình Medallion cục bộ từ Bronze -> Silver -> Toàn bộ các mô hình Gold
pipeline-full-local: bronze-run silver-run gold-lgbm-run gold-bkt-run
	@echo "🎉 [SUCCESS] Toàn bộ hệ thống định hình dữ liệu lớn đã hoàn thành cục bộ!"

# ====================================================================
# ⚡ NRT INFERENCE (NEAR-REAL-TIME MICRO-BATCH — MỖI 15 PHÚT)
# ====================================================================

# Chạy NRT Inference thủ công cục bộ (test nhanh)
nrt-inference-run:
	python -m data_pipeline.jobs.nrt_gold_inference

# Triển khai K8s CronJob NRT lên AKS (mỗi 15 phút tự động)
k8s-deploy-nrt:
	kubectl apply -f infra/manifests/oulad-nrt-cronjob.yaml
	@echo "✅ NRT CronJob deployed: chạy mỗi 15 phút tự động."
	kubectl get cronjob oulad-nrt-inference-cronjob -n blearn-medallion

# Kích hoạt NRT Job ngay lập tức (manual trigger để test)
k8s-nrt-trigger-once:
	kubectl create job --from=cronjob/oulad-nrt-inference-cronjob nrt-manual-$$(date +%s) -n blearn-medallion
	@echo "⚡ NRT job triggered manually. Check logs:"
	@echo "  kubectl get jobs -n blearn-medallion | grep nrt-manual"

# ====================================================================
# 🛡️ FAILOVER: K8s NATIVE CRONJOBS (DỰ PHÒNG KHI AIRFLOW LỖI)
# ====================================================================
# Kiến trúc Active-Passive: Airflow là Primary, K8s CronJobs là Passive.
# Khi Airflow xảy ra sự cố, chạy 'make k8s-activate-failover-schedule'
# để kích hoạt lịch K8s thay thế. Chạy 'deactivate' khi Airflow phục hồi.

# Kích hoạt toàn bộ lịch Failover K8s (khi Airflow lỗi)
k8s-activate-failover-schedule:
	@echo "🚨 [FAILOVER] Activating K8s Native CronJob schedules..."
	kubectl apply -f infra/manifests/oulad-bronze-cronjob.yaml
	kubectl apply -f infra/manifests/oulad-silver-cronjob.yaml
	kubectl apply -f infra/manifests/oulad-nrt-cronjob.yaml
	@echo "✅ [FAILOVER] Lịch dự phòng đã kích hoạt:"
	@echo "   • oulad-bronze-cronjob    → 02:00 UTC hàng ngày"
	@echo "   • oulad-silver-gold-cronjob → 03:00 UTC hàng ngày"
	@echo "   • oulad-nrt-cronjob       → mỗi 15 phút"
	kubectl get cronjobs -n blearn-medallion

# Tắt lịch Failover K8s (khi Airflow đã phục hồi)
k8s-deactivate-failover-schedule:
	@echo "✅ [FAILOVER] Deactivating K8s CronJobs (Airflow back online)..."
	kubectl delete cronjob oulad-bronze-cronjob -n blearn-medallion --ignore-not-found=true
	kubectl delete cronjob oulad-silver-gold-cronjob -n blearn-medallion --ignore-not-found=true
	@echo "   NRT CronJob giữ nguyên — chạy song song với Airflow là an toàn."
	kubectl get cronjobs -n blearn-medallion

# Kiểm tra trạng thái tất cả CronJobs và Jobs đang chạy
k8s-failover-status:
	@echo "📊 CronJob status:"
	kubectl get cronjobs -n blearn-medallion
	@echo "\n📋 Recent Jobs:"
	kubectl get jobs -n blearn-medallion --sort-by=.metadata.creationTimestamp | tail -10

# ====================================================================
# 🏗️ AIRFLOW HA: NÂNG CẤP LÊN KUBERNETES EXECUTOR + 2 SCHEDULERS
# ====================================================================

# Nâng cấp Airflow lên cấu hình HA (KubernetesExecutor + 2 Schedulers)
# Yêu cầu: Helm đã cài sẵn và đang có kết nối tới AKS cluster
airflow-upgrade-ha:
	@echo "🔧 Upgrading Airflow to HA (KubernetesExecutor + 2 Schedulers)..."
	helm upgrade blearn-airflow apache-airflow/airflow \
		--namespace blearn-medallion \
		--values infra/airflow-values.yaml \
		--atomic \
		--timeout 10m
	@echo "✅ Airflow HA upgrade complete. Check scheduler pods:"
	kubectl get pods -n blearn-medallion -l component=scheduler

# ====================================================================
# 📺 KAFKA STREAMING & TOPIC MANAGEMENT UTILITIES
# ====================================================================
.PHONY: kafka-topics-list kafka-consume-stream kafka-produce-test

# 1. Liệt kê toàn bộ các topics đang hoạt động trên cụm Kafka KRaft
kafka-topics-list:
	@echo "🔍 Đang quét danh sách các Topics trên cụm Kafka KRaft..."
	kubectl exec kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# 2. Lắng nghe trực tiếp dòng sự kiện click chuột thời gian thực (Live Clickstream Monitor)
kafka-consume-stream:
	@echo "📺 Đang theo dõi luồng dữ liệu thời gian thực từ topic 'learning-events'..."
	@echo "💡 Bấm click chuột trên Streamlit Dashboard để thấy sự kiện nhảy về đây real-time."
	kubectl exec -it kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic learning-events --from-beginning

# 3. Giả lập bắn một lượng lớn clickstream thử nghiệm vào Kafka để test tải (Load Testing)
kafka-produce-test:
	@echo "🚀 Đang bắn chuỗi tương tác học liệu mẫu vào Kafka Broker..."
	kubectl exec -i kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic learning-events <<< '{"student_id_hash":"test_portfolio_student_hash","id_site":"1001","date":0,"sum_click":5}'
	@echo "✅ Đã phát tán sự kiện mẫu thành công."

# ====================================================================
# 🧹 APACHE ICEBERG DATA MAINTENANCE (BRONZE COMPACTION)
# ====================================================================
.PHONY: k8s-iceberg-compact

# 4. Kích hoạt lệnh nén tệp nhỏ (Data Compaction) cho tầng Bronze Iceberg để tối ưu hiệu năng đọc ghi
k8s-iceberg-compact:
	@echo "🧹 Đang khởi chạy Spark Session để thực hiện dọn dẹp và nén tệp nhỏ (Data Compaction) cho bảng oulad_studentvle..."
	kubectl exec -i deployment/blearn-streamlit-ui -n blearn-medallion -- python3 -c " \
		from data_pipeline.ingestion.ingest import build_spark; \
		import os; \
		account = os.getenv('AZURE_STORAGE_ACCOUNT', 'stblearnminhdata2026'); \
		root = f'abfss://gold@{account}.dfs.core.windows.net/iceberg_warehouse/gold/'; \
		spark = build_spark('Iceberg_Compaction_Utility', root, iceberg_catalogs={'bronze_catalog': 'bronze'}); \
		print('⚙️ Đang thực thi lệnh OPTIMIZE COMPACT trên tầng Bronze...'); \
		spark.sql('ALTER TABLE bronze_catalog.full_db.oulad_studentvle EXECUTE optimize WHERE date IS NOT NULL'); \
		print('🎉 Chu trình nén tệp nhỏ (Data Compaction) hoàn thành xuất sắc!'); \
		spark.stop();"

# ====================================================================
# 🟢 GREEN-OPS: SUSPEND / RESUME STREAMING & MLOPS ARCHITECTURE
# ====================================================================
.PHONY: streaming-resume streaming-suspend

# 🟢 ĐÁNH THỨC TOÀN BỘ KIẾN TRÚC STREAMING VÀ MLOPS INFRA (Khi bắt đầu demo)
streaming-resume:
	@echo "🔋 Đang đánh thức cụm Kafka KRaft, Spark Streaming và FastAPI Gateway..."
	kubectl scale statefulset kafka-stream -n blearn-medallion --replicas=1
	kubectl scale deployment spark-streaming-job -n blearn-medallion --replicas=1
	kubectl scale deployment blearn-api-gateway -n blearn-medallion --replicas=1
	kubectl scale deployment kube-prometheus-stack-grafana -n blearn-medallion --replicas=1
	kubectl scale deployment -l release=kube-prometheus-stack -n blearn-medallion --replicas=1
	kubectl scale statefulset prometheus-kube-prometheus-stack-prometheus -n blearn-medallion --replicas=1
	@echo "✅ Tất cả các cấu phần streaming đã live, sẵn sàng phục vụ!"

# 🔴 ĐÓNG BĂNG TOÀN BỘ HỆ THỐNG ĐỂ TIẾT KIỆM CREDIT (Ngay sau khi demo xong)
streaming-suspend:
	@echo "🛑 Đang hạ số lượng bản ghi (replicas) về 0 để đóng băng tài nguyên cụm..."
	kubectl scale statefulset kafka-stream -n blearn-medallion --replicas=0
	kubectl scale deployment spark-streaming-job -n blearn-medallion --replicas=0
	kubectl scale deployment blearn-api-gateway -n blearn-medallion --replicas=0
	kubectl scale deployment kube-prometheus-stack-grafana -n blearn-medallion --replicas=0
	kubectl scale deployment -l release=kube-prometheus-stack -n blearn-medallion --replicas=0
	kubectl scale statefulset prometheus-kube-prometheus-stack-prometheus -n blearn-medallion --replicas=0
	@echo "😴 Đã ngủ đông thành công! Hệ thống tiêu thụ 0% CPU/RAM, bảo toàn Credit Azure."

# 🎯 TẮT VẬT LÝ TOÀN BỘ CỤM AKS (Đưa tiền thuê máy về 0đ khi không làm việc)
cluster-stop:
	@echo "🛑 Đang phát lệnh tắt nguồn vật lý cụm máy ảo AKS đám mây..."
	az aks stop --name aks-blearn-dev --resource-group RG-BLEarn-Compute
	@echo "💤 Cụm AKS đã ngủ đông vật lý thành công. Toàn bộ tài nguyên tính toán đã ngừng tính phí!"

# ⚡ BẬT LẠI NGUỒN VẬT LÝ CỤM AKS (Chạy trước khi demo 3-5 phút)
cluster-start:
	@echo "⚡ Đang khởi động lại nguồn vật lý hệ thống máy chủ AKS..."
	az aks start --name aks-blearn-dev --resource-group RG-BLEarn-Compute
	@echo "🚀 Cụm AKS đã trực tuyến trở lại! Hãy chạy 'make streaming-resume' sau khi các Node sẵn sàng."
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

# --- Azure Infrastructure ---
aks-start:
	az aks start --name aks-blearn-dev --resource-group RG-BLEarn-Compute

aks-stop:
	az aks stop --name aks-blearn-dev --resource-group RG-BLEarn-Compute

k8s-status:
	kubectl get jobs,pods -n blearn-medallion

# --- Local / Dev Pipeline ---
bronze-run:
	python -m data_pipeline.ingestion.ingest --manifest-path full_data_manifest.json --output-root abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/full/ ingest --namespace full

silver-run:
	python -m data_pipeline.jobs.silver_transform

gold-lgbm-run:
	python -m data_pipeline.jobs.gold_transform_and_train

gold-bkt-run:
	python -m data_pipeline.jobs.gold_bkt_pipeline

gold-recsys-run:
	python -m data_pipeline.jobs.gold_recsys_pipeline

serving-export-run:
	python -m data_pipeline.jobs.export_to_serving

streamlit-local-run:
	streamlit run dashboard/app.py

api-local-run:
	uvicorn dashboard.api_server:app --reload

react-local-install:
	cd frontend-dashboard && npm install

react-local-run:
	cd frontend-dashboard && npm run dev

react-local-build:
	cd frontend-dashboard && npm run build

k8s-deploy-api:
	kubectl apply -f infra/manifests/api-serving.yaml

deploy-ops:
	kubectl apply -f infra/manifests/management-services.yaml

k8s-api-status:
	kubectl get svc blearn-api-service -n blearn-medallion

# --- K8s One-Shot Test Jobs ---
k8s-test-bkt:
	kubectl delete job oulad-gold-bkt-test -n blearn-medallion --ignore-not-found=true
	kubectl apply -f infra/manifests/oulad-bkt-test.yaml
	@echo "Waiting for pod initialization..."
	sleep 5
	kubectl logs -f $$(kubectl get pods -n blearn-medallion -l job-name=oulad-gold-bkt-test -o jsonpath='{.items[0].metadata.name}') -n blearn-medallion

k8s-serving-export:
	kubectl delete job oulad-serving-export-job -n blearn-medallion --ignore-not-found=true
	kubectl apply -f infra/manifests/oulad-serving-export-job.yaml
	@echo "Waiting for pod initialization..."
	sleep 5
	kubectl logs -f job/oulad-serving-export-job -n blearn-medallion

k8s-deploy-streamlit:
	kubectl apply -f infra/manifests/streamlit-dashboard.yaml

k8s-streamlit-status:
	kubectl get svc blearn-streamlit-service -n blearn-medallion

k8s-clean-test:
	kubectl delete jobs --all -n blearn-medallion

# --- End-to-End Automation Flow ---
pipeline-full-local: bronze-run silver-run gold-lgbm-run gold-bkt-run
	@echo "Full pipeline finished locally."

# --- NRT Inference ---
nrt-inference-run:
	python -m data_pipeline.jobs.nrt_gold_inference

k8s-deploy-nrt:
	kubectl apply -f infra/manifests/oulad-nrt-cronjob.yaml
	@echo "NRT CronJob deployed."
	kubectl get cronjob oulad-nrt-inference-cronjob -n blearn-medallion

k8s-nrt-trigger-once:
	kubectl create job --from=cronjob/oulad-nrt-inference-cronjob nrt-manual-$$(date +%s) -n blearn-medallion
	@echo "NRT job triggered manually."

# --- K8s CronJob Failover (Active-Passive) ---
k8s-activate-failover-schedule:
	@echo "Activating K8s Native CronJob schedules..."
	kubectl apply -f infra/manifests/oulad-bronze-cronjob.yaml
	kubectl apply -f infra/manifests/oulad-silver-cronjob.yaml
	kubectl apply -f infra/manifests/oulad-nrt-cronjob.yaml
	kubectl get cronjobs -n blearn-medallion

k8s-deactivate-failover-schedule:
	@echo "Deactivating K8s CronJobs..."
	kubectl delete cronjob oulad-bronze-cronjob -n blearn-medallion --ignore-not-found=true
	kubectl delete cronjob oulad-silver-gold-cronjob -n blearn-medallion --ignore-not-found=true
	kubectl get cronjobs -n blearn-medallion

k8s-failover-status:
	@echo "CronJob status:"
	kubectl get cronjobs -n blearn-medallion
	@echo "\nRecent Jobs:"
	kubectl get jobs -n blearn-medallion --sort-by=.metadata.creationTimestamp | tail -10

# --- Kafka topic management ---
kafka-topics-list:
	kubectl exec kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

kafka-consume-stream:
	kubectl exec kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic learning-events --partitions 1 --replication-factor 1 --if-not-exists 2>/dev/null || true
	kubectl exec -it kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic learning-events --from-beginning

kafka-produce-test:
	kubectl exec -i kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic learning-events <<< '{"student_id_hash":"test_portfolio_student_hash","id_site":"1001","date":0,"sum_click":5}'

# --- Apache Iceberg maintenance ---
k8s-iceberg-compact:
	kubectl exec -i deployment/blearn-streamlit-ui -n blearn-medallion -- python3 -c " \
		from data_pipeline.ingestion.ingest import build_spark; \
		import os; \
		account = os.getenv('AZURE_STORAGE_ACCOUNT', 'stblearnminhdata2026'); \
		root = f'abfss://gold@{account}.dfs.core.windows.net/iceberg_warehouse/gold/'; \
		spark = build_spark('Iceberg_Compaction_Utility', root, iceberg_catalogs={'bronze_catalog': 'bronze'}); \
		spark.sql('ALTER TABLE bronze_catalog.full_db.oulad_studentvle EXECUTE optimize WHERE date IS NOT NULL'); \
		spark.stop();"

# --- GreenOps Control ---
streaming-resume:
	kubectl scale statefulset kafka-stream -n blearn-medallion --replicas=1
	kubectl scale deployment spark-streaming-job -n blearn-medallion --replicas=1
	kubectl scale deployment blearn-api-gateway -n blearn-medallion --replicas=1
	kubectl scale deployment kube-prometheus-stack-grafana -n blearn-medallion --replicas=1
	kubectl scale deployment -l release=kube-prometheus-stack -n blearn-medallion --replicas=1
	kubectl scale statefulset prometheus-kube-prometheus-stack-prometheus -n blearn-medallion --replicas=1

streaming-suspend:
	kubectl scale statefulset kafka-stream -n blearn-medallion --replicas=0
	kubectl scale deployment spark-streaming-job -n blearn-medallion --replicas=0
	kubectl scale deployment blearn-api-gateway -n blearn-medallion --replicas=0
	kubectl scale deployment kube-prometheus-stack-grafana -n blearn-medallion --replicas=0
	kubectl scale deployment -l release=kube-prometheus-stack -n blearn-medallion --replicas=0
	kubectl scale statefulset prometheus-kube-prometheus-stack-prometheus -n blearn-medallion --replicas=0

streaming-load-test:
	$(PYTHON) -m data_pipeline.utils.traffic_generator

cluster-stop:
	az aks stop --name aks-blearn-dev --resource-group RG-BLEarn-Compute

cluster-start:
	az aks start --name aks-blearn-dev --resource-group RG-BLEarn-Compute

# --- Live Demo & Testing ---
demo-wait-ready:
	@kubectl wait --for=condition=ready pod -l app=api-gateway -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=frontend-demo -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=kafka -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=spark-streaming -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=redis -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=mlflow -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=nessie -n blearn-medallion --timeout=300s

demo-prep:
	az aks start --name aks-blearn-dev --resource-group RG-BLEarn-Compute
	kubectl scale deployment blearn-api-gateway -n blearn-medallion --replicas=1
	kubectl scale deployment blearn-frontend-demo -n blearn-medallion --replicas=1
	kubectl scale statefulset kafka-stream -n blearn-medallion --replicas=1
	kubectl scale deployment spark-streaming-job -n blearn-medallion --replicas=1
	@$(MAKE) demo-wait-ready

demo-connect:
	-pkill -f "port-forward" || true
	@$(MAKE) demo-wait-ready
	@nohup kubectl port-forward deployment/blearn-api-gateway 8000:8000 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward deployment/blearn-frontend-demo 8080:80 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/kafka-service 9092:29092 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/redis-service 6379:6379 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/mlflow-service 5005:5000 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/nessie-service 19120:19120 -n blearn-medallion >/dev/null 2>&1 &
	@echo "Tunnels established."

demo-smoke-test:
	kubectl exec -it kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic learning-events --from-beginning | grep assessment_submission

demo-reset:
	@token=$$(curl -s -X POST http://localhost:8000/login -H "Content-Type: application/json" -d '{"username": "demo-admin", "role": "admin"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token',''))"); \
	if [ -n "$$token" ]; then \
	    res=$$(curl -s -X POST http://localhost:8000/reset-assessment-shifts -H "Authorization: Bearer $$token"); \
	    echo "Reset shifts: $$res"; \
	else \
	    echo "Failed to retrieve admin token."; \
	    exit 1; \
	fi

demo-reset-deep:
	-kubectl scale deployment/spark-streaming-job --replicas=0 -n blearn-medallion
	-kubectl exec -n blearn-medallion deployment/blearn-streamlit-ui -- python3 -c "from data_pipeline.ingestion.ingest import build_spark; spark = build_spark('Reset', 'abfss://gold@$(AZURE_STORAGE_ACCOUNT).dfs.core.windows.net/iceberg_warehouse/gold/', iceberg_catalogs={'silver_catalog': 'silver', 'gold_catalog': 'gold'}); spark.sql('TRUNCATE TABLE silver_catalog.silver_db.oulad_studentassessment'); spark.sql('TRUNCATE TABLE gold_catalog.gold_db.oulad_at_risk_predictions'); spark.stop()"
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system bronze --name checkpoints --yes 2>/dev/null || true
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system silver --name checkpoints --yes 2>/dev/null || true
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system gold --name checkpoints --yes 2>/dev/null || true
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system gold --name iceberg_warehouse/checkpoints --yes 2>/dev/null || true
	-kubectl scale deployment/spark-streaming-job --replicas=1 -n blearn-medallion
	@token=$$(curl -s -X POST http://localhost:8000/login -H "Content-Type: application/json" -d '{"username": "demo-admin", "role": "admin"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token',''))"); \
	if [ -n "$$token" ]; then \
	    res=$$(curl -s -X POST http://localhost:8000/reset-assessment-shifts -H "Authorization: Bearer $$token"); \
	    echo "Reset shifts: $$res"; \
	else \
	    echo "Failed to retrieve admin token."; \
	fi

demo-status:
	kubectl get pods -n blearn-medallion
	@echo ""
	kubectl top pods -n blearn-medallion
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
	@echo "🔧 Đang tự động kiểm tra và đảm bảo topic 'learning-events' tồn tại..."
	kubectl exec kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic learning-events --partitions 1 --replication-factor 1 --if-not-exists 2>/dev/null || true
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
.PHONY: streaming-resume streaming-suspend streaming-load-test

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

# 📡 Sinh lưu lượng clickstream phục vụ demo realtime và kiểm thử chịu tải
streaming-load-test:
	$(PYTHON) -m data_pipeline.utils.traffic_generator

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

# ====================================================================
# 🎯 LIVE DEMO & TESTING WORKFLOW UTILITIES
# ====================================================================
.PHONY: demo-prep demo-connect demo-smoke-test demo-reset demo-reset-deep demo-wait-ready demo-status

# Đợi đầy đủ pod demo cốt lõi và pod quản trị chuyển sang Ready
demo-wait-ready:
	@echo "⏳ Đang chờ các pod demo sẵn sàng..."
	@kubectl wait --for=condition=ready pod -l app=api-gateway -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=frontend-demo -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=kafka -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=spark-streaming -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=redis -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=mlflow -n blearn-medallion --timeout=300s
	@kubectl wait --for=condition=ready pod -l app=nessie -n blearn-medallion --timeout=300s
	@echo "✅ Các pod demo đã sẵn sàng."

# 1. Chuẩn bị môi trường, kiểm tra tính sẵn sàng của cụm hạ tầng
demo-prep:
	@echo "🔋 Đang kiểm tra trạng thái và đánh thức toàn bộ tài nguyên..."
	az aks start --name aks-blearn-dev --resource-group RG-BLEarn-Compute
	kubectl scale deployment blearn-api-gateway -n blearn-medallion --replicas=1
	kubectl scale deployment blearn-frontend-demo -n blearn-medallion --replicas=1
	kubectl scale statefulset kafka-stream -n blearn-medallion --replicas=1
	kubectl scale deployment spark-streaming-job -n blearn-medallion --replicas=1
	@$(MAKE) demo-wait-ready
	@echo "✅ Các cấu phần cốt lõi đã được đặt tỷ lệ replica = 1."

# 2. Mở cổng kết nối nhanh API Gateway, Frontend và các dịch vụ quản trị về máy Mac
demo-connect:
	@echo "🔌 Đang kết nối và chuyển tiếp cổng về máy Mac..."
	@echo "   • API Gateway: http://localhost:8000"
	@echo "   • Frontend Demo: http://localhost:8080"
	@echo "   • Kafka Broker: localhost:9092"
	@echo "   • Redis: localhost:6379"
	@echo "   • MLflow Server: http://localhost:5005"
	@echo "   • Project Nessie: http://localhost:19120"
	-pkill -f "port-forward" || true
	@$(MAKE) demo-wait-ready
	@nohup kubectl port-forward deployment/blearn-api-gateway 8000:8000 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward deployment/blearn-frontend-demo 8080:80 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/kafka-service 9092:29092 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/redis-service 6379:6379 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/mlflow-service 5005:5000 -n blearn-medallion >/dev/null 2>&1 &
	@nohup kubectl port-forward service/nessie-service 19120:19120 -n blearn-medallion >/dev/null 2>&1 &
	@echo "✅ Tunnels established in background."

# 3. Lắng nghe tức thì phản hồi nộp bài tập từ phía sinh viên
demo-smoke-test:
	@echo "📺 Đang theo dõi luồng phản hồi khép kín (Closed-Loop Assessment Submissions)..."
	kubectl exec -it kafka-stream-0 -n blearn-medallion -- /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic learning-events --from-beginning | grep assessment_submission

# 4. Reset trạng thái rủi ro bỏ học (độ dịch chuyển) về mặc định ban đầu để bắt đầu demo mới
demo-reset:
	@echo "=== ĐANG RESET NHANH TRẠNG THÁI DEMO QUA GATEWAY ==="
	@token=$$(curl -s -X POST http://localhost:8000/login -H "Content-Type: application/json" -d '{"username": "demo-admin", "role": "admin"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token',''))"); \
	if [ -n "$$token" ]; then \
	    res=$$(curl -s -X POST http://localhost:8000/reset-assessment-shifts -H "Authorization: Bearer $$token"); \
	    echo "✅ API Gateway reset: $$res"; \
	else \
	    echo "⚠️ Không lấy được Token đăng nhập của Admin."; \
	    exit 1; \
	fi
	@echo "=== DEMO ĐÃ ĐƯỢC RESET VỀ BASELINE NHANH ==="

demo-reset-deep:
	@echo "=== ĐANG KHỞI TẠO LẠI TRẠNG THÁI HỆ THỐNG DEMO (DEEP CLEAN) ==="
	# 1. Hạ số lượng bản sao pod streaming về 0 để ngắt luồng ghi dữ liệu
	-kubectl scale deployment/spark-streaming-job --replicas=0 -n blearn-medallion
	
	# 2. Thực thi script python dọn sạch bảng Iceberg
	-kubectl exec -n blearn-medallion deployment/blearn-streamlit-ui -- python3 -c "from data_pipeline.ingestion.ingest import build_spark; spark = build_spark('Reset', 'abfss://gold@$(AZURE_STORAGE_ACCOUNT).dfs.core.windows.net/iceberg_warehouse/gold/', iceberg_catalogs={'silver_catalog': 'silver', 'gold_catalog': 'gold'}); spark.sql('TRUNCATE TABLE silver_catalog.silver_db.oulad_studentassessment'); spark.sql('TRUNCATE TABLE gold_catalog.gold_db.oulad_at_risk_predictions'); spark.stop()"
	
	# 3. Xóa thư mục checkpoint cũ trên Azure Storage
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system bronze --name checkpoints --yes 2>/dev/null || true
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system silver --name checkpoints --yes 2>/dev/null || true
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system gold --name checkpoints --yes 2>/dev/null || true
	-az storage fs directory delete --account-name $(AZURE_STORAGE_ACCOUNT) --file-system gold --name iceberg_warehouse/checkpoints --yes 2>/dev/null || true
	
	# 4. Scale pod streaming lên lại mốc 1 để sẵn sàng hấp thụ dòng dữ liệu mới
	-kubectl scale deployment/spark-streaming-job --replicas=1 -n blearn-medallion
	
	# 5. Gọi API Gateway reset in-memory shifts
	@token=$$(curl -s -X POST http://localhost:8000/login -H "Content-Type: application/json" -d '{"username": "demo-admin", "role": "admin"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token',''))"); \
	if [ -n "$$token" ]; then \
	    res=$$(curl -s -X POST http://localhost:8000/reset-assessment-shifts -H "Authorization: Bearer $$token"); \
	    echo "✅ API Gateway reset: $$res"; \
	else \
	    echo "⚠️ Không lấy được Token đăng nhập của Admin."; \
	fi
	@echo "=== HỆ THỐNG ĐÃ RESET THÀNH CÔNG VỀ TRẠNG THÁI SẠCH ==="

# 5. In ra bảng tổng hợp tình trạng hoạt động (CPU, RAM, Uptime) của toàn bộ các pod thành phần
demo-status:
	@echo "===================================================================="
	@echo "📊 BLEarn Kubernetes Cluster Pod Status & Health Check"
	@echo "===================================================================="
	@kubectl get pods -n blearn-medallion
	@echo ""
	@echo "===================================================================="
	@echo "📈 Resource Utilization (CPU & Memory)"
	@echo "===================================================================="
	@kubectl top pods -n blearn-medallion

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

.PHONY: help bronze-discover-full bronze-consolidate-ednet bronze-full-manifest bronze-full-ingest bronze-full-verify bronze-full-audit bronze-full-flow silver-oulad-transform gold-oulad-train gold-bkt-run medallion-oulad-flow infra-terraform-init infra-terraform-plan infra-terraform-apply

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
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

.PHONY: help bronze-discover-full bronze-consolidate-ednet bronze-full-manifest bronze-full-ingest bronze-full-verify bronze-full-audit bronze-full-flow silver-oulad-transform gold-oulad-train medallion-oulad-flow infra-terraform-init infra-terraform-plan infra-terraform-apply

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
		--output-namespace silver_db \
		--output-root "$(SILVER_OUTPUT_ROOT)"

gold-oulad-train:
	$(PYTHON) -m data_pipeline.gold.oulad \
		--input-catalog silver_catalog \
		--input-namespace silver_db \
		--output-catalog gold_catalog \
		--output-namespace gold_db \
		--output-root "$(GOLD_OUTPUT_ROOT)"

medallion-oulad-flow: silver-oulad-transform gold-oulad-train

infra-terraform-init:
	cd $(INFRA_DIR) && $(TERRAFORM) init

infra-terraform-plan:
	cd $(INFRA_DIR) && $(TERRAFORM) plan

infra-terraform-apply:
	cd $(INFRA_DIR) && $(TERRAFORM) apply
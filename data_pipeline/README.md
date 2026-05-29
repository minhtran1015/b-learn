Data Pipeline
=============

This folder contains the **Bronze ingestion pipeline** for B-Learn datasets (EdNet, OULAD, SED).

## Architecture: Medallion Pattern

The pipeline implements the Medallion (Bronze-Silver-Gold) data architecture:

| Layer | Purpose | Storage | Format | Automation |
|-------|---------|---------|--------|-----------|
| **Landing** | Raw data uploaded by users/sources | ADLS Gen2 or local | CSV, JSON, Markdown | Manual upload or scheduled connectors |
| **Bronze** | Light-processed, queryable tables with metadata | ADLS Gen2 (production) or local | Parquet (or Iceberg) | PySpark ingestion pipeline (currently manual, target: AKS scheduled job) |
| **Silver** | Cleaned, deduplicated, enriched data | ADLS Gen2 | Iceberg (recommended) | dbt or custom Spark jobs |
| **Gold** | Business-ready aggregated datasets | ADLS Gen2 | Iceberg | dbt or Spark SQL views |

**Current Status**: You have successfully ingested the subset to Bronze (64 records → 22 tables on ADLS).

## Prerequisites

The pipeline requires Java 21+ access to internal modules. Before running any ingest/verify commands, export the Java options:

```bash
export JDK_JAVA_OPTIONS="--add-opens=java.base/java.lang=ALL-UNNAMED \
--add-opens=java.base/java.lang.invoke=ALL-UNNAMED \
--add-opens=java.base/java.lang.reflect=ALL-UNNAMED \
--add-opens=java.base/java.io=ALL-UNNAMED \
--add-opens=java.base/java.net=ALL-UNNAMED \
--add-opens=java.base/java.nio=ALL-UNNAMED \
--add-opens=java.base/java.util=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED \
--add-opens=java.base/sun.nio.ch=ALL-UNNAMED \
--add-opens=java.base/sun.nio.cs=ALL-UNNAMED \
--add-opens=java.base/sun.security.action=ALL-UNNAMED \
--add-opens=java.base/sun.util.calendar=ALL-UNNAMED \
--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED"
```

**Tip**: Add this to `~/.zshrc` to avoid re-entering on every terminal session.

## Usage

The pipeline uses PySpark 3.5.1 (Java 21 compatible) and includes:
- `data_pipeline/ingestion/` - CLI orchestration
- `data_pipeline/utils/` - Shared helpers (manifest, reader)
- `data_pipeline/jobs/` - Dataset-specific defaults

### Workflow

1. **Discover** - Scan source data and create manifest:
```bash
python -m data_pipeline.ingestion.ingest \
  --source-root small-data \
  --manifest-path small_data_manifest.json \
  discover
```

2. **Ingest** - Load into Bronze (Parquet):
```bash
python -m data_pipeline.ingestion.ingest \
  --manifest-path small_data_manifest.json \
  --output-root infra/bronze/ \
  ingest
```

3. **Verify** - Compare source counts with Bronze row counts:
```bash
python -m data_pipeline.ingestion.ingest \
  --manifest-path small_data_manifest.json \
  --output-root infra/bronze/ \
  verify
```

## Cloud-First Subset Validation (ADLS Gen2)

Run subset first before full data:

1. Export Azure Storage key:
```bash
export AZURE_STORAGE_KEY="<YOUR_ACCOUNT_KEY>"
```

2. Discover subset manifest:
```bash
python -m data_pipeline.ingestion.ingest \
  --source-root small-data \
  --manifest-path subset_cloud_manifest.json \
  discover
```

3. Ingest subset to ADLS Bronze:
```bash
python -m data_pipeline.ingestion.ingest \
  --source-root small-data \
  --manifest-path subset_cloud_manifest.json \
  --output-root "abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/subset_tables/" \
  ingest
```

Notes:
- The pipeline auto-enables Azure Spark configs when `--output-root` starts with `abfss://`.
- By default it uses storage account `stblearnminhdata2026` (override with `AZURE_STORAGE_ACCOUNT` if needed).

## OULAD Silver/Gold Deployment

The infra-first OULAD path is driven through the repository `Makefile` and Iceberg catalogs:

```bash
make silver-oulad-transform
make gold-oulad-train
make medallion-oulad-flow
```

These targets read Bronze OULAD tables from `bronze_catalog.full_db`, write Silver tables to `silver_catalog.silver_db`, and then build Gold features plus a LightGBM baseline on top of Silver.

## Configuration

Default locations (from repo root):
- **Source**: `small-data/` (EdNet, OULAD, SED demo data)
- **Manifest**: `infra/ingest/small_data_manifest.jsonl`
- **Output**: `infra/bronze/` (local Parquet)

Override with CLI flags:
```bash
python -m data_pipeline.ingestion.ingest \
  --source-root large-data \
  --manifest-path custom_manifest.json \
  --output-root /path/to/bronze \
  discover
```

## Production Deployment

For production (Iceberg/ABFS), update:
1. Spark config in `ingestion/ingest.py:build_spark()`
2. Output format from Parquet to Iceberg
3. Partition strategy for time-based queries

See comments in ingest.py for Iceberg integration points.

## Automation Strategy (Production)

### Current (Development)
- Manual trigger: Run `python -m data_pipeline.ingestion.ingest ...` from local machine
- Testing: Subset validation before full data ingest

### Target (Production on AKS)

1. **Scheduled Trigger** (Airflow, CronJob, or Azure Functions):
   ```bash
   # Example: Kubernetes CronJob or Airflow DAG
   python -m data_pipeline.ingestion.ingest \
     --source-root "abfss://landing@stblearnminhdata2026.dfs.core.windows.net/" \
     --output-root "abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/" \
     ingest
   ```

2. **Resource Placement**: Run on AKS cluster (not local Mac) to leverage:
   - Distributed Spark executors
   - Larger memory/CPU for full EdNet dataset
   - Network proximity to cloud storage

3. **Monitoring**: Log ingest counts and verification reports to:
   - `_ingest_counts.json` (row counts per table)
   - `_verification_report.json` (source vs. bronze match validation)

### Why Iceberg for Production

Replace Parquet with Apache Iceberg when moving to production:

| Feature | Parquet | Iceberg |
|---------|---------|---------|
| ACID Transactions | ❌ | ✅ |
| Schema Evolution | ⚠️ (manual) | ✅ (automatic) |
| Time Travel | ❌ | ✅ |
| Partition Evolution | ❌ (rebuild) | ✅ (in-place) |
| Small Files Problem | ⚠️ (manual compaction) | ✅ (automatic) |

**For B-Learn**: With 1.7M EdNet files, Iceberg's automatic file management and schema flexibility are critical.

**Upgrade Steps** (see code comments for details):
1. Add `org.apache.iceberg:iceberg-spark-runtime` to Spark config
2. Change `.format("parquet")` → `.format("iceberg")` in write operations
3. Update catalog config for Iceberg metadata layer
4. Test schema evolution by adding new EdNet event types

## Production Deployment

For production (Iceberg/ABFS), update:
1. Spark config in `ingestion/ingest.py:build_spark()`
2. Output format from Parquet to Iceberg
3. Partition strategy for time-based queries

See comments in ingest.py for Iceberg integration points.

## Full EdNet Preparation (Consolidation)

Before full ingest, consolidate many small `u*.csv` files:

```bash
python -m data_pipeline.ingestion.ingest \
  consolidate-ednet \
  --ednet-source-root large-data/EdNet \
  --consolidated-root infra/staging/ednet_consolidated \
  --target-partitions 10
```

Then run discover/ingest from the consolidated root (or feed it into your next Bronze stage).

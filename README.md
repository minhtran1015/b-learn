# b-learn

B-Learn is a Bronze-ingestion workspace for EdNet, OULAD, SED, and content datasets.

## Bronze Flow

The top-level `Makefile` packages the full Bronze workflow so you can run the same sequence every time:

1. Consolidate EdNet into larger parquet groups.
2. Build the full manifest.
3. Ingest into Iceberg `full_db` on Azure Storage.
4. Verify row counts against the manifest.
5. Sample audit metadata columns on the cloud tables.

## OULAD Medallion Flow

The repository now also includes an infra-first OULAD Silver/Gold path for the student-at-risk use case:

1. `make silver-oulad-transform` cleans OULAD Bronze into Iceberg Silver tables on ADLS.
2. `make gold-oulad-train` materializes Gold features, trains LightGBM, and writes predictions plus model artifacts.
3. `make medallion-oulad-flow` runs Silver then Gold in sequence.
4. Terraform now provisions an AKS CronJob that periodically clones `https://github.com/minhtran1015/b-learn.git` and runs the same Silver -> Gold pipeline in-cluster.

## System Documentation & Reports

Comprehensive documentation of the system architecture and analytical engines is available:
- **System Architecture**: Read the [Medallion Architecture Documentation](file:///Users/trandinhquangminh/Codespace/b-learn/docs/medallion_architecture.md) for details on the Bronze consolidation, Silver anonymization, LightGBM feature engineering, and AKS cluster infrastructure.
- **Gold BKT Engine**: Read the [Gold BKT Pipeline Report](file:///Users/trandinhquangminh/Codespace/b-learn/docs/bkt_pipeline_report.md) for root-cause analyses on pyBKT memory bottlenecks, parameter tuning, and sequential iterator loop implementation details.

## Prerequisites

Set these environment variables before running the full cloud flow:

- `SPARK_DRIVER_MEMORY=8g`
- `AZURE_STORAGE_KEY=<your Azure Storage account key>`

The pipeline defaults to `stblearnminhdata2026` as the storage account. Override `AZURE_STORAGE_ACCOUNT` if your environment uses a different account.

## Common Commands

From the repository root:

```bash
make bronze-consolidate-ednet
make bronze-full-manifest
make bronze-full-ingest
make bronze-full-verify
make bronze-full-audit
```

To run the entire sequence in one shot:

```bash
SPARK_DRIVER_MEMORY=8g AZURE_STORAGE_KEY="<your key>" make bronze-full-flow
```

## Notes

- `bronze-full-ingest` writes to `abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/full/`.
- `bronze-full-verify` should return `ok: true` with no mismatches before you consider the Bronze layer complete.
- `bronze-full-audit` samples `_ingest_at`, `_source_file`, and `_source_dataset` from `bronze_catalog.full_db.ednet_kt1_events` and `bronze_catalog.full_db.oulad_studentinfo`.

## Serving Layer & Streamlit Dashboard

To provide a zero-cost, high-speed UI interaction tier, we implemented a **File-Driven (Parquet + DuckDB)** serving layer:

1. **Serving Export Job**: Reads the Gold Iceberg tables (dropout predictions, BKT mastery status, LightGCN embeddings) and exports them as optimized flat Parquet files to the `serving` container in Azure Blob Storage.
2. **Streamlit UI**: Loads the Parquet files into memory. Performs a real-time matrix dot-product on user-item embeddings via NumPy to recommend resources in under 1 millisecond.

### Troubleshooting and Resolutions

* **Problem**: Streamlit crashed at startup with `File does not exist: dashboard/app.py`.
  * **Cause**: The `Dockerfile` did not copy the `dashboard/` directory, only `data_pipeline/`. Additionally, the container runtime environment ran from a different working directory.
  * **Resolution**:
    1. Added `COPY dashboard/ /app/dashboard/` to the [Dockerfile](file:///Users/trandinhquangminh/Codespace/b-learn/Dockerfile).
    2. Updated the Kubernetes Deployment command in [streamlit-dashboard.yaml](file:///Users/trandinhquangminh/Codespace/b-learn/infra/manifests/streamlit-dashboard.yaml) to use the absolute path `/app/dashboard/app.py`.
    3. Triggered a CI/CD rebuild to push the updated Docker image to Azure Container Registry (ACR).

### Human-Readable Presentation Refinement

* **Friendly Dropdowns**: Rather than showing raw 64-character SHA-256 hash strings (e.g. `24c8b...`), the sidebar selection uses Streamlit's `format_func` to display user friendly IDs like `👤 Học viên #1 (24c8b...)`. This keeps the dropdown clean and structured for live demonstrations while retaining the original hash for filtering.
* **Student Profile Headers**: Displayed a clean metadata card showing the student index and the full SHA-256 Cloud ID inside the main page.

### Deploying the Serving Tier

Make targets are available to manage the serving layer and UI deployment:

```bash
# Export Gold tables to serving parquet files (on AKS)
make k8s-serving-export

# Deploy or update the Streamlit Dashboard deployment on AKS
make k8s-deploy-streamlit

# View LoadBalancer external IP and status
make k8s-streamlit-status
```
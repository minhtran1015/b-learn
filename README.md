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
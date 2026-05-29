# Bronze ingestion for `small-data`

This folder contains a local-first Spark pipeline for creating Bronze parquet tables from the checked-in `small-data/` tree.

## What it does

- `discover`: walks `small-data/` and writes a JSONL manifest of every supported source file
- `ingest`: reads the manifest, loads CSV/JSON/Markdown sources, adds Bronze metadata, and writes parquet outputs
- `verify`: compares source row counts with Bronze row counts and writes a JSON report

The script is designed so the output root can later point at Azure Storage using `abfss://...` without changing the ingestion logic.

## Supported sources

- `small-data/EdNet/KT1`, `KT2`, `KT3`, `KT4`
- `small-data/EdNet/contents/*.csv`
- `small-data/Question_Bank.json` and `small-data/Lecture_Bank.json`
- `small-data/SED/*.csv`
- `small-data/OULAD/*.csv`
- `small-data/Data/**/*.md`

## Metadata added to every Bronze record

- `_ingest_at`
- `_ingest_date`
- `_source_file`
- `_source_dataset`

## Local run

```bash
cd /Users/trandinhquangminh/Codespace/b-learn
python infra/ingest/bronze_ingest.py discover
python infra/ingest/bronze_ingest.py ingest
python infra/ingest/bronze_ingest.py verify
```

By default, parquet output is written to `infra/bronze/` and the manifest is written to `infra/ingest/small_data_manifest.jsonl`.

## Azure run

Override the paths and point `--output-root` to your Bronze container, for example:

```bash
python infra/ingest/bronze_ingest.py \
  --source-root /mnt/staging/small-data \
  --output-root abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/tables \
  ingest
```

## Notes

- SED `Student_log.csv` automatically adds `event_date` and partitions by that derived date.
- OULAD tables partition by `code_module` when that column exists.
- EdNet files are grouped by logical dataset and preserved with per-file source lineage.

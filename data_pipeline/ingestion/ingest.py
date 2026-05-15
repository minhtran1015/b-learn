#!/usr/bin/env python3
"""Entrypoint for Bronze ingestion located under data_pipeline/.

This module orchestrates discovery, ingestion and verification using the
`data_pipeline/utils` helpers. It mirrors the previous infra/ingest behavior
but is organized for maintainability: jobs/ contains dataset-specific code,
utils/ contains shared helpers, and ingestion/ contains the CLI.

=== Medallion Architecture Implementation ===

Landing Layer → Bronze Layer → Silver Layer → Gold Layer

This pipeline implements the **Bronze Layer** (light processing + metadata):
- Reads raw CSV/JSON/Markdown from Landing (local or ADLS landing zone)
- Adds Bronze metadata columns (_ingest_at, _source_file, _dataset)
- Applies light schema fixes and transformations
- Writes queryable Parquet tables (targets Iceberg for production)

Current Status (May 2026):
✓ Successfully ingested subset (64 source records → 22 Bronze tables)
✓ Cloud output validation on ADLS Gen2 (abfss://bronze@...)
✓ Ready for full EdNet consolidation + production automation

Next Steps:
- Transition automation from local (Mac) to AKS cluster
- Upgrade storage format from Parquet to Apache Iceberg
- Implement Silver layer (dbt/Spark SQL cleaning and enrichment)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from functools import reduce
from itertools import islice
from pathlib import Path
from typing import Dict

os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from utils.manifest import discover_files, load_manifest, normalize_table_name, write_manifest
from utils.reader import (
    read_csv_as_bronze_df,
    read_json_bronze_df,
    read_markdown_bronze_df,
    add_bronze_metadata,
    ensure_text_column,
)


DEFAULT_AZURE_STORAGE_ACCOUNT = "stblearnminhdata2026"


def is_cloud_path(path_value: Path | str) -> bool:
    return str(path_value).startswith("abfss://")


def require_azure_storage_key() -> str:
    storage_account_key = os.getenv("AZURE_STORAGE_KEY")
    if not storage_account_key:
        raise ValueError(
            "AZURE_STORAGE_KEY is required when using ADLS output paths (abfss://...). "
            "Export it first, then retry."
        )
    return storage_account_key


def build_spark(
    app_name: str,
    output_root: Path | str | None = None,
    *,
    heavy_local_job: bool = False,
    shuffle_partitions: int = 4,
) -> SparkSession:
    local_master = "local[4]" if heavy_local_job else "local[*]"
    builder = (
        SparkSession.builder.appName(app_name)
        .master(local_master)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.sql.session.timeZone", "UTC")
    )

    if heavy_local_job:
        builder = (
            builder
            .config("spark.driver.memory", "8g")
            .config("spark.executor.memory", "8g")
            .config("spark.memory.fraction", "0.6")
            .config("spark.memory.storageFraction", "0.3")
            .config("spark.default.parallelism", "8")
        )

    if output_root is not None and is_cloud_path(output_root):
        storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT", DEFAULT_AZURE_STORAGE_ACCOUNT)
        storage_account_key = require_azure_storage_key()
        
        # Iceberg warehouse path on Azure ADLS Gen2
        warehouse_path = f"abfss://bronze@{storage_account_name}.dfs.core.windows.net/iceberg_warehouse"
        
        # Iceberg 1.5.0 with Spark 3.5 runtime (Scala 2.12)
        builder = (
            builder
            .config(
                "spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
                "org.apache.hadoop:hadoop-azure:3.3.4,"
                "com.microsoft.azure:azure-storage:7.0.1",
            )
            .config(
                f"spark.hadoop.fs.azure.account.key.{storage_account_name}.dfs.core.windows.net",
                storage_account_key,
            )
            # Iceberg SQL Extensions and Catalog configuration
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            .config("spark.sql.catalog.bronze_catalog", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.bronze_catalog.type", "hadoop")
            .config("spark.sql.catalog.bronze_catalog.warehouse", warehouse_path)
            # Optimization for small files (EdNet: 1.7M files) - auto-compact to 128MB
            .config("spark.sql.catalog.bronze_catalog.write.target-file-size-bytes", "134217728")  # 128MB
        )

    return builder.getOrCreate()


def bronze_output_path(output_root: Path | str, table_name: str) -> str:
    root = str(output_root).rstrip("/")
    return f"{root}/{table_name}"


def write_table(df, output_root: Path | str, table_name: str, partition_hint: str, namespace: str = "demo") -> None:
    """Write Bronze table using Iceberg Catalog (hadoop type) on Azure ADLS Gen2.
    
    Args:
        namespace: 'demo' or 'full' - determines Iceberg database name (demo_db or full_db)
    """
    if is_cloud_path(output_root):
        # Cloud: Use Iceberg Catalog with hadoop type for ACID guarantees and metadata management
        # Table identifier: bronze_catalog.{demo_db|full_db}.{table}
        db_name = f"{namespace}_db"
        table_identifier = f"bronze_catalog.{db_name}.{table_name}"
        
        # Write using writeTo() with createOrReplace for Iceberg table management
        writer = df.writeTo(table_identifier).tableProperty("write.format.default", "parquet")
        
        if partition_hint and partition_hint in df.columns:
            writer = writer.partitionedBy(partition_hint)
        
        writer.createOrReplace()
    else:
        # Local: Use Parquet format with snappy compression
        output_path = bronze_output_path(output_root, table_name)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        writer = df.write.format("parquet").option("compression", "snappy").mode("overwrite")
        if partition_hint and partition_hint in df.columns:
            writer = writer.partitionBy(partition_hint)
        writer.save(output_path)


def ingest_manifest(spark: SparkSession, manifest_path: Path, output_root: Path | str, source_root: Path, namespace: str = "demo") -> Dict[str, int]:
    counts: Dict[str, int] = {}
    grouped_records: Dict[str, list[dict[str, str]]] = {}

    for record in load_manifest(manifest_path):
        grouped_records.setdefault(record["table"], []).append(record)

    for table, records in grouped_records.items():
        file_type = records[0]["file_type"]
        dataset = records[0]["dataset"]
        partition_hint = records[0].get("partition_hint", "_ingest_date")
        dataframes = []

        for record in records:
            file_path = Path(record["source_path"])

            if file_type == "csv":
                bronze_df = read_csv_as_bronze_df(spark, file_path)
                if dataset == "sed" and file_path.name == "Student_log.csv":
                    bronze_df = ensure_text_column(bronze_df, "timecreated")
                    bronze_df = bronze_df.withColumn(
                        "event_date",
                        F.to_date(F.to_timestamp(F.col("timecreated"), "yyyy-MM-dd HH:mm:ss")),
                    )
                    partition_hint = "event_date"

                if dataset == "oulad" and "code_module" not in bronze_df.columns:
                    bronze_df = bronze_df.withColumn("code_module", F.lit(None).cast("string"))

                bronze_df = add_bronze_metadata(bronze_df, dataset, str(file_path))
                dataframes.append(bronze_df)
                continue

            if file_type == "json":
                bronze_df = read_json_bronze_df(spark, file_path)
                bronze_df = add_bronze_metadata(bronze_df, dataset, str(file_path))
                dataframes.append(bronze_df)
                continue

            if file_type == "markdown":
                bronze_df = read_markdown_bronze_df(spark, file_path, source_root)
                bronze_df = add_bronze_metadata(bronze_df, dataset, str(file_path))
                dataframes.append(bronze_df)
                continue

            raise ValueError(f"Unsupported file type for {file_path}: {record.get('ingest_strategy', file_type)}")

        if not dataframes:
            continue

        bronze_df = reduce(lambda left, right: left.unionByName(right, allowMissingColumns=True), dataframes)
        write_table(bronze_df, output_root, table, partition_hint, namespace=namespace)
        counts[table] = bronze_df.count()

    return counts


def count_bronze_rows(spark: SparkSession, output_root: Path | str):
    output_root_str = str(output_root)
    counts = {}
    if "://" in output_root_str:
        return counts

    output_root_path = Path(output_root_str)
    if not output_root_path.exists():
        return counts

    for table_dir in sorted(output_root_path.iterdir()):
        if not table_dir.is_dir():
            continue
        if not list(table_dir.rglob("*.parquet")):
            continue
        counts[table_dir.name] = spark.read.parquet(str(table_dir)).count()
    return counts


def run_discover(args: argparse.Namespace) -> None:
    source_root = Path(args.source_root).resolve()
    manifest_path = Path(args.manifest_path).resolve()
    records = discover_files(source_root)
    write_manifest(records, manifest_path)
    print(json.dumps({"manifest_path": str(manifest_path), "record_count": len(records)}, indent=2))


def run_ingest(args: argparse.Namespace) -> None:
    """Ingest manifest records into Bronze layer.
    
    Bronze Layer Definition (Medallion Architecture):
    - INPUT: Raw Landing data (CSV, JSON) from small-data/ or ADLS landing zone
    - PROCESSING: Light transformation
      * Add metadata columns (_ingest_at, _source_file, _dataset)
      * Handle schema fixes (e.g., add missing code_module for OULAD)
      * Parse timestamps and create partition columns (e.g., event_date)
    - OUTPUT: Queryable Parquet (or Iceberg) tables on ADLS Bronze zone
    
    Difference from Upload:
    - Upload: Move raw CSV to cloud (Landing layer)
    - Ingest: Transform + load into queryable format (Bronze layer)
    
    This is NOT just copying files; it's light processing to enable fast queries.
    """
    spark = build_spark("B-Learn_Bronze_Ingest", args.output_root)
    try:
        source_root = Path(args.source_root).resolve()
        manifest_path = Path(args.manifest_path).resolve()
        output_root = args.output_root
        namespace = getattr(args, 'namespace', 'demo')  # Default to 'demo' if not specified
        counts = ingest_manifest(spark, manifest_path, output_root, source_root, namespace=namespace)
        report_path = manifest_path.parent / "_ingest_counts.json"
        report_path.write_text(json.dumps(counts, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"output_root": str(output_root), "tables": counts}, indent=2, sort_keys=True))
    finally:
        spark.stop()


def run_verify(args: argparse.Namespace) -> None:
    spark = build_spark("B-Learn_Bronze_Verify", args.output_root)
    try:
        source_root = Path(args.source_root).resolve()
        manifest_path = Path(args.manifest_path).resolve()
        output_root = args.output_root
        manifest_records = load_manifest(manifest_path)
        counts_report_path = manifest_path.parent / "_ingest_counts.json"
        if counts_report_path.exists():
            bronze_counts = json.loads(counts_report_path.read_text(encoding="utf-8"))
        else:
            bronze_counts = count_bronze_rows(spark, output_root)

        source_counts = {}
        for record in manifest_records:
            file_path = Path(record["source_path"])
            table = record["table"]
            file_type = record["file_type"]

            if file_type == "csv":
                source_counts[table] = source_counts.get(table, 0) + sum(1 for _ in file_path.open("r", encoding="utf-8-sig")) - 1
            elif file_type == "json":
                parsed = json.loads(file_path.read_text(encoding="utf-8"))
                source_counts[table] = source_counts.get(table, 0) + (len(parsed) if isinstance(parsed, list) else 1)
            elif file_type == "markdown":
                source_counts[table] = source_counts.get(table, 0) + 1

        rows = []
        all_tables = sorted(set(source_counts) | set(bronze_counts))
        ok = True
        for table in all_tables:
            source_count = source_counts.get(table, 0)
            bronze_count = bronze_counts.get(table, 0)
            matched = source_count == bronze_count
            ok = ok and matched
            rows.append({
                "table": table,
                "source_count": source_count,
                "bronze_count": bronze_count,
                "match": matched,
            })

        report = {"ok": ok, "rows": rows}
        report_path = manifest_path.parent / "_verification_report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        raise SystemExit(0 if ok else 1)
    finally:
        spark.stop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bronze ingestion pipeline for B-Learn datasets")
    repo_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--source-root", default=str(repo_root / "small-data"), help="Root folder containing small-data")
    parser.add_argument("--manifest-path", default=str(repo_root / "infra" / "ingest" / "small_data_manifest.jsonl"), help="Path for the JSONL manifest")
    parser.add_argument("--output-root", default=str(repo_root / "infra" / "bronze"), help="Root folder for bronze parquet outputs")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover", help="Create a manifest for the small-data tree")
    ingest_parser = subparsers.add_parser("ingest", help="Run Spark ingestion using the manifest")
    ingest_parser.add_argument(
        "--namespace",
        choices=["demo", "full"],
        default="demo",
        help="Iceberg namespace: 'demo' (demo_db) for testing, 'full' (full_db) for production data",
    )
    subparsers.add_parser("verify", help="Compare source counts with bronze output counts")

    consolidate_parser = subparsers.add_parser(
        "consolidate-ednet",
        help="Consolidate many small EdNet CSVs into larger Parquet files before full ingest",
    )
    consolidate_parser.add_argument(
        "--ednet-source-root",
        default=str(repo_root / "large-data" / "EdNet"),
        help="Root folder for full EdNet source (expects KT1..KT4 and optional contents)",
    )
    consolidate_parser.add_argument(
        "--consolidated-root",
        default=str(repo_root / "infra" / "staging" / "ednet_consolidated"),
        help="Output root for consolidated Parquet tables",
    )
    consolidate_parser.add_argument(
        "--target-partitions",
        type=int,
        default=10,
        help="Target number of output partitions per group (tune by cluster size and data volume)",
    )
    consolidate_parser.add_argument(
        "--batch-size",
        type=int,
        default=250,
        help="Number of source CSV files to read per batch during consolidation (lower avoids OOM)",
    )

    return parser


def chunk_files(files: list[Path], chunk_size: int):
    iterator = iter(files)
    while True:
        batch = list(islice(iterator, chunk_size))
        if not batch:
            break
        yield batch


def consolidate_ednet_group(
    spark: SparkSession,
    source_files: list[Path],
    output_path: str,
    target_partitions: int,
    batch_size: int,
) -> int:
    total_rows = 0
    for batch_index, file_batch in enumerate(chunk_files(source_files, batch_size)):
        batch_paths = [str(path) for path in file_batch]
        df = spark.read.option("header", "true").csv(batch_paths)
        batch_rows = df.count()
        total_rows += batch_rows
        (
            df.repartition(target_partitions)
            .write.mode("overwrite" if batch_index == 0 else "append")
            .parquet(output_path)
        )
    return total_rows


def consolidate_single_csv(
    spark: SparkSession,
    source_file: Path,
    output_path: str,
    target_partitions: int,
) -> int:
    df = spark.read.option("header", "true").csv(str(source_file))
    row_count = df.count()
    (
        df.repartition(target_partitions)
        .write.mode("overwrite")
        .parquet(output_path)
    )
    return row_count


def run_consolidate_ednet(args: argparse.Namespace) -> None:
    spark = build_spark(
        "B-Learn_EdNet_Consolidation",
        args.consolidated_root,
        heavy_local_job=True,
        shuffle_partitions=max(16, args.target_partitions * 2),
    )
    try:
        ednet_root = Path(args.ednet_source_root).resolve()
        output_root = str(args.consolidated_root).rstrip("/")
        target_partitions = args.target_partitions
        batch_size = args.batch_size
        groups = ["KT1", "KT2", "KT3", "KT4"]

        results: dict[str, int] = {}
        for group in groups:
            source_dir = ednet_root / group
            matching_files = sorted(source_dir.glob("u*.csv"))
            output_path = f"{output_root}/{group.lower()}"
            if not matching_files:
                results[group.lower()] = 0
                continue
            results[group.lower()] = consolidate_ednet_group(
                spark,
                matching_files,
                output_path,
                target_partitions,
                batch_size,
            )

        contents_dir = ednet_root / "contents"
        contents_files = sorted(contents_dir.glob("*.csv"))
        if contents_files:
            for source_file in contents_files:
                table_name = normalize_table_name(source_file.stem)
                contents_output = f"{output_root}/contents/{table_name}"
                results[f"contents_{table_name}"] = consolidate_single_csv(
                    spark,
                    source_file,
                    contents_output,
                    max(1, target_partitions // 2),
                )
        else:
            results["contents"] = 0

        print(
            json.dumps(
                {
                    "ednet_source_root": str(ednet_root),
                    "consolidated_root": output_root,
                    "target_partitions": target_partitions,
                    "rows": results,
                },
                indent=2,
                sort_keys=True,
            )
        )
    finally:
        spark.stop()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "discover":
        run_discover(args)
    elif args.command == "ingest":
        run_ingest(args)
    elif args.command == "verify":
        run_verify(args)
    elif args.command == "consolidate-ednet":
        run_consolidate_ednet(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Automated Bronze-layer ingestion for the small-data datasets.

The app has three commands:
- discover: walk the small-data tree and write a JSONL manifest
- ingest: read the manifest, load source files with PySpark, add Bronze metadata,
  and write parquet outputs grouped by logical table
- verify: compare source row counts with bronze parquet row counts

The implementation is intentionally local-first so it can run against the
checked-in small-data folders. The output root can later be pointed at Azure
Storage (abfss://...) without changing the ingestion logic.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from functools import reduce
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = ROOT / "small-data"
DEFAULT_OUTPUT_ROOT = ROOT / "infra" / "bronze"
DEFAULT_MANIFEST_PATH = ROOT / "infra" / "ingest" / "small_data_manifest.jsonl"


@dataclass(frozen=True)
class ManifestRecord:
    source_path: str
    dataset: str
    table: str
    file_type: str
    partition_hint: str
    ingest_strategy: str

    def to_json(self) -> str:
        return json.dumps({
            "source_path": self.source_path,
            "dataset": self.dataset,
            "table": self.table,
            "file_type": self.file_type,
            "partition_hint": self.partition_hint,
            "ingest_strategy": self.ingest_strategy,
        }, ensure_ascii=False)


def build_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def normalize_table_name(value: str) -> str:
    result = []
    previous_underscore = False
    for char in value.lower():
        if char.isalnum():
            result.append(char)
            previous_underscore = False
        else:
            if not previous_underscore:
                result.append("_")
                previous_underscore = True
    normalized = "".join(result).strip("_")
    return normalized or "table"


def resolve_dataset_record(source_root: Path, file_path: Path) -> ManifestRecord | None:
    relative = file_path.relative_to(source_root)
    parts = relative.parts

    if not parts:
        return None

    top_level = parts[0]
    suffix = file_path.suffix.lower()

    if len(parts) == 1 and file_path.name == "Question_Bank.json":
        return ManifestRecord(
            source_path=str(file_path),
            dataset="content",
            table="content_question_bank",
            file_type="json",
            partition_hint="_ingest_date",
            ingest_strategy="json",
        )

    if len(parts) == 1 and file_path.name == "Lecture_Bank.json":
        return ManifestRecord(
            source_path=str(file_path),
            dataset="content",
            table="content_lecture_bank",
            file_type="json",
            partition_hint="_ingest_date",
            ingest_strategy="json",
        )

    if top_level == "EdNet":
        if len(parts) >= 3 and parts[1] in {"KT1", "KT2", "KT3", "KT4"} and suffix == ".csv":
            table_map = {
                "KT1": "ednet_kt1_events",
                "KT2": "ednet_kt2_events",
                "KT3": "ednet_kt3_events",
                "KT4": "ednet_kt4_events",
            }
            return ManifestRecord(
                source_path=str(file_path),
                dataset="ednet",
                table=table_map[parts[1]],
                file_type="csv",
                partition_hint="_ingest_date",
                ingest_strategy="csv",
            )

        if len(parts) >= 3 and parts[1] == "contents" and suffix == ".csv":
            stem = normalize_table_name(file_path.stem)
            return ManifestRecord(
                source_path=str(file_path),
                dataset="ednet",
                table=f"ednet_{stem}",
                file_type="csv",
                partition_hint="_ingest_date",
                ingest_strategy="csv",
            )

        if suffix == ".json":
            if file_path.name == "Question_Bank.json":
                return ManifestRecord(
                    source_path=str(file_path),
                    dataset="ednet",
                    table="ednet_question_bank",
                    file_type="json",
                    partition_hint="_ingest_date",
                    ingest_strategy="json",
                )
            if file_path.name == "Lecture_Bank.json":
                return ManifestRecord(
                    source_path=str(file_path),
                    dataset="ednet",
                    table="ednet_lecture_bank",
                    file_type="json",
                    partition_hint="_ingest_date",
                    ingest_strategy="json",
                )

    if top_level == "SED" and suffix == ".csv":
        stem = normalize_table_name(file_path.stem)
        return ManifestRecord(
            source_path=str(file_path),
            dataset="sed",
            table=f"sed_{stem}",
            file_type="csv",
            partition_hint="_ingest_date",
            ingest_strategy="csv",
        )

    if top_level == "OULAD" and suffix == ".csv":
        stem = normalize_table_name(file_path.stem)
        partition_hint = "code_module" if stem != "studentvle" else "code_module"
        return ManifestRecord(
            source_path=str(file_path),
            dataset="oulad",
            table=f"oulad_{stem}",
            file_type="csv",
            partition_hint=partition_hint,
            ingest_strategy="csv",
        )

    if top_level == "Data" and suffix == ".md":
        stem = normalize_table_name(file_path.stem)
        return ManifestRecord(
            source_path=str(file_path),
            dataset="content",
            table="content_documents",
            file_type="markdown",
            partition_hint="chapter",
            ingest_strategy=f"markdown:{stem}",
        )

    return None


def discover_files(source_root: Path) -> list[ManifestRecord]:
    records: list[ManifestRecord] = []

    root_question_bank = source_root / "Question_Bank.json"
    root_lecture_bank = source_root / "Lecture_Bank.json"

    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.name in {"Question_Bank.json", "Lecture_Bank.json"} and file_path.parent.name == "EdNet":
            # Prefer the canonical root-level copies to avoid duplicate ingest.
            if (file_path.name == root_question_bank.name and root_question_bank.exists()) or (
                file_path.name == root_lecture_bank.name and root_lecture_bank.exists()
            ):
                continue

        record = resolve_dataset_record(source_root, file_path)
        if record is not None:
            records.append(record)

    return records


def write_manifest(records: Iterable[ManifestRecord], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.to_json())
            handle.write("\n")


def load_manifest(manifest_path: Path) -> list[dict[str, str]]:
    records = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def read_header_row(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    cleaned = []
    for index, column in enumerate(header):
        value = column.strip()
        if not value:
            value = f"_row_idx" if index == 0 else f"col_{index}"
        cleaned.append(value)
    return cleaned


def read_csv_as_bronze_df(spark: SparkSession, file_path: Path) -> DataFrame:
    columns = read_header_row(file_path)
    raw_df = spark.read.option("header", True).option("inferSchema", False).csv(str(file_path))

    if len(raw_df.columns) != len(columns):
        raise ValueError(
            f"Column count mismatch for {file_path}: header has {len(columns)} columns, Spark read {len(raw_df.columns)}"
        )

    return raw_df.toDF(*columns)


def read_json_bronze_df(spark: SparkSession, file_path: Path, dataset: str, table: str) -> DataFrame:
    raw_text = file_path.read_text(encoding="utf-8")
    frame = spark.read.option("multiLine", True).json(str(file_path))
    return frame.withColumn("_raw_json", F.lit(raw_text))


def read_markdown_bronze_df(spark: SparkSession, file_path: Path, source_root: Path) -> DataFrame:
    relative = file_path.relative_to(source_root)
    chapter = relative.parts[1] if len(relative.parts) > 1 else relative.parts[0]
    content = file_path.read_text(encoding="utf-8")
    rows = [
        Row(
            path=str(file_path),
            chapter=chapter,
            filename=file_path.name,
            content_text=content,
        )
    ]
    return spark.createDataFrame(rows)


def add_bronze_metadata(df: DataFrame, dataset: str, source_path: str) -> DataFrame:
    return (
        df.withColumn("_ingest_at", F.current_timestamp())
        .withColumn("_ingest_date", F.current_date())
        .withColumn("_source_file", F.lit(source_path))
        .withColumn("_source_dataset", F.lit(dataset))
    )


def ensure_text_column(df: DataFrame, column_name: str) -> DataFrame:
    if column_name in df.columns:
        return df
    return df.withColumn(column_name, F.lit(None).cast(StringType()))


def bronze_output_path(output_root: Path | str, table_name: str) -> str:
    root = str(output_root).rstrip("/")
    return f"{root}/{table_name}"


def write_table(df: DataFrame, output_root: Path | str, table_name: str, partition_hint: str) -> None:
    writer = df.write.mode("overwrite").format("parquet").option("compression", "snappy")

    if partition_hint in df.columns:
        writer = writer.partitionBy(partition_hint)

    output_path = bronze_output_path(output_root, table_name)
    output_root_str = str(output_root)
    if "://" not in output_root_str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    writer.save(output_path)


def ingest_manifest(spark: SparkSession, manifest_path: Path, output_root: Path | str, source_root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    grouped_records: dict[str, list[dict[str, str]]] = {}

    for record in load_manifest(manifest_path):
        grouped_records.setdefault(record["table"], []).append(record)

    for table, records in grouped_records.items():
        file_type = records[0]["file_type"]
        dataset = records[0]["dataset"]
        partition_hint = records[0].get("partition_hint", "_ingest_date")
        dataframes: list[DataFrame] = []

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
                    bronze_df = bronze_df.withColumn("code_module", F.lit(None).cast(StringType()))

                bronze_df = add_bronze_metadata(bronze_df, dataset, str(file_path))
                dataframes.append(bronze_df)
                continue

            if file_type == "json":
                bronze_df = read_json_bronze_df(spark, file_path, dataset, table)
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
        write_table(bronze_df, output_root, table, partition_hint)
        counts[table] = bronze_df.count()

    return counts


def count_bronze_rows(spark: SparkSession, output_root: Path | str) -> dict[str, int]:
    output_root_str = str(output_root)
    counts: dict[str, int] = {}
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
    spark = build_spark("B-Learn_Bronze_Ingest")
    try:
        source_root = Path(args.source_root).resolve()
        manifest_path = Path(args.manifest_path).resolve()
        output_root = args.output_root
        counts = ingest_manifest(spark, manifest_path, output_root, source_root)
        report_path = manifest_path.parent / "_ingest_counts.json"
        report_path.write_text(json.dumps(counts, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"output_root": str(output_root), "tables": counts}, indent=2, sort_keys=True))
    finally:
        spark.stop()


def run_verify(args: argparse.Namespace) -> None:
    spark = build_spark("B-Learn_Bronze_Verify")
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

        source_counts: dict[str, int] = {}
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
    parser = argparse.ArgumentParser(description="Bronze ingestion pipeline for B-Learn small-data")
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT), help="Root folder containing small-data")
    parser.add_argument("--manifest-path", default=str(DEFAULT_MANIFEST_PATH), help="Path for the JSONL manifest")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Root folder for bronze parquet outputs")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover", help="Create a manifest for the small-data tree")
    subparsers.add_parser("ingest", help="Run Spark ingestion using the manifest")
    subparsers.add_parser("verify", help="Compare source counts with bronze output counts")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "discover":
        run_discover(args)
    elif args.command == "ingest":
        run_ingest(args)
    elif args.command == "verify":
        run_verify(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
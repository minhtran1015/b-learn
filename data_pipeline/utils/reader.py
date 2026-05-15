from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType


def read_header_row(file_path: Path) -> List[str]:
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


def read_json_bronze_df(spark: SparkSession, file_path: Path) -> DataFrame:
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

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from ingestion.ingest import _abfss_container, build_spark, write_table
from jobs.oulad import SOURCE_TABLES

DEFAULT_INPUT_CATALOG = "bronze_catalog"
DEFAULT_INPUT_NAMESPACE = "full_db"
DEFAULT_OUTPUT_CATALOG = "silver_catalog"
DEFAULT_OUTPUT_NAMESPACE = "silver_db"
DEFAULT_OUTPUT_ROOT = (
    f"abfss://silver@{os.getenv('AZURE_STORAGE_ACCOUNT', 'stblearnminhdata2026')}"
    ".dfs.core.windows.net/iceberg_warehouse/silver/"
)

INT_COLUMNS = {
    "id_assessment",
    "id_site",
    "date",
    "date_submitted",
    "date_registration",
    "date_unregistration",
    "is_banked",
    "module_presentation_length",
    "num_of_prev_attempts",
    "studied_credits",
    "sum_click",
    "week_from",
    "week_to",
    "id_parent",
}

DOUBLE_COLUMNS = {
    "score",
    "weight",
}


def _trim_string_columns(df: DataFrame) -> DataFrame:
    for field in df.schema.fields:
        if field.dataType.simpleString() == "string":
            df = df.withColumn(field.name, F.trim(F.col(field.name)))
    return df


def _cast_columns(df: DataFrame, int_columns: set[str], double_columns: set[str]) -> DataFrame:
    for column_name in int_columns:
        if column_name in df.columns:
            df = df.withColumn(column_name, F.col(column_name).cast("int"))
    for column_name in double_columns:
        if column_name in df.columns:
            df = df.withColumn(column_name, F.col(column_name).cast("double"))
    return df


def _hash_student_id(df: DataFrame) -> DataFrame:
    if "id_student" in df.columns:
        df = df.withColumn("id_student", F.sha2(F.col("id_student").cast("string"), 256))
    return df


def _add_silver_metadata(df: DataFrame, source_table: str) -> DataFrame:
    return (
        df.withColumn("_silver_at", F.current_timestamp())
        .withColumn("_silver_source_table", F.lit(source_table))
    )


def _clean_table(table_name: str, df: DataFrame) -> DataFrame:
    df = _trim_string_columns(df)
    df = _cast_columns(df, INT_COLUMNS, DOUBLE_COLUMNS)
    df = _hash_student_id(df)

    if table_name == "oulad_studentinfo":
        df = df.withColumn("num_of_prev_attempts", F.col("num_of_prev_attempts").cast("int"))
        df = df.withColumn("studied_credits", F.col("studied_credits").cast("int"))
    elif table_name == "oulad_studentregistration":
        df = df.withColumn("date_registration", F.col("date_registration").cast("int"))
        df = df.withColumn("date_unregistration", F.col("date_unregistration").cast("int"))
    elif table_name == "oulad_studentassessment":
        df = df.withColumn("id_assessment", F.col("id_assessment").cast("int"))
        df = df.withColumn("date_submitted", F.col("date_submitted").cast("int"))
        df = df.withColumn("is_banked", F.col("is_banked").cast("int"))
        df = df.withColumn("score", F.col("score").cast("double"))
    elif table_name == "oulad_studentvle":
        df = df.withColumn("id_site", F.col("id_site").cast("int"))
        df = df.withColumn("date", F.col("date").cast("int"))
        df = df.withColumn("sum_click", F.col("sum_click").cast("int"))
    elif table_name == "oulad_assessments":
        df = df.withColumn("id_assessment", F.col("id_assessment").cast("int"))
        df = df.withColumn("date", F.col("date").cast("int"))
        df = df.withColumn("weight", F.col("weight").cast("double"))
    elif table_name == "oulad_courses":
        df = df.withColumn("module_presentation_length", F.col("module_presentation_length").cast("int"))
    elif table_name == "oulad_vle":
        if "id_site" in df.columns:
            df = df.withColumn("id_site", F.col("id_site").cast("int"))
        if "week_from" in df.columns:
            df = df.withColumn("week_from", F.col("week_from").cast("int"))
        if "week_to" in df.columns:
            df = df.withColumn("week_to", F.col("week_to").cast("int"))
        if "id_parent" in df.columns:
            df = df.withColumn("id_parent", F.col("id_parent").cast("int"))

    return df.dropDuplicates()


def materialize_silver(
    spark,
    input_catalog: str,
    input_namespace: str,
    output_root: str,
    output_catalog: str,
    output_namespace: str,
) -> None:
    for table_name in SOURCE_TABLES:
        bronze_table = f"{input_catalog}.{input_namespace}.{table_name}"
        df = spark.table(bronze_table)
        cleaned = _add_silver_metadata(_clean_table(table_name, df), table_name)
        write_table(
            cleaned,
            output_root,
            table_name,
            partition_hint="code_module" if "code_module" in cleaned.columns else "_silver_at",
            namespace=output_namespace,
            catalog_name=output_catalog,
        )
        print(f"Wrote silver table: {output_catalog}.{output_namespace}.{table_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize OULAD Silver tables from Bronze Iceberg")
    parser.add_argument("--input-catalog", default=DEFAULT_INPUT_CATALOG)
    parser.add_argument("--input-namespace", default=DEFAULT_INPUT_NAMESPACE)
    parser.add_argument("--output-catalog", default=DEFAULT_OUTPUT_CATALOG)
    parser.add_argument("--output-namespace", default=DEFAULT_OUTPUT_NAMESPACE)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--input-container", default="bronze")
    parser.add_argument("--output-container", default="silver")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not str(args.output_root).startswith("abfss://"):
        raise ValueError("Silver job is intended for ADLS deployment; pass an abfss:// output root.")

    spark = build_spark(
        "B-Learn_Silver_OULAD",
        args.output_root,
        iceberg_catalogs={args.input_catalog: args.input_container, args.output_catalog: args.output_container},
        default_catalog_name=args.output_catalog,
    )
    try:
        materialize_silver(
            spark,
            args.input_catalog,
            args.input_namespace,
            args.output_root,
            args.output_catalog,
            args.output_namespace,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

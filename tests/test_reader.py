import sys
from pathlib import Path
import pytest
from pyspark.sql import SparkSession

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data_pipeline.utils.reader import (
    read_header_row,
    add_bronze_metadata,
    ensure_text_column
)

@pytest.fixture(scope="module")
def spark():
    # Initialize a local SparkSession for testing
    spark_session = SparkSession.builder \
        .master("local[*]") \
        .appName("test-reader-pyspark") \
        .config("spark.sql.session.timeZone", "UTC") \
        .getOrCreate()
    yield spark_session
    spark_session.stop()

def test_read_header_row(tmp_path):
    csv_file = tmp_path / "test.csv"
    # Write a test csv with some leading/trailing spaces and empty column names
    csv_file.write_text("col1, col2 ,  , col4\nval1,val2,val3,val4", encoding="utf-8-sig")
    
    headers = read_header_row(csv_file)
    assert headers == ["col1", "col2", "col_2", "col4"]

def test_add_bronze_metadata(spark):
    data = [("Alice", 1)]
    schema = ["name", "age"]
    df = spark.createDataFrame(data, schema)
    
    res = add_bronze_metadata(df, "test_dataset", "test_path")
    assert "_ingest_at" in res.columns
    assert "_ingest_date" in res.columns
    assert "_source_file" in res.columns
    assert "_source_dataset" in res.columns

def test_ensure_text_column(spark):
    data = [("Alice", 1)]
    schema = ["name", "age"]
    df = spark.createDataFrame(data, schema)
    
    # Column already exists: should return original dataframe directly
    res = ensure_text_column(df, "name")
    assert "name" in res.columns
    assert len(res.columns) == 2
    
    # Column does not exist: should add it
    res2 = ensure_text_column(df, "disability")
    assert "disability" in res2.columns
    assert len(res2.columns) == 3

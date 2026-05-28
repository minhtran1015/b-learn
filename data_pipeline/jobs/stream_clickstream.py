import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# Add root data_pipeline to sys.path to resolve import module
PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

def build_streaming_spark():
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    storage_account_key = os.getenv("AZURE_STORAGE_KEY")
    
    # Configure Spark with Apache Iceberg and Kafka package extensions
    builder = (
        SparkSession.builder
        .appName("B-Learn_Clickstream_Streaming")
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.jars.packages", 
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
                "org.apache.hadoop:hadoop-azure:3.3.4,"
                "com.microsoft.azure:azure-storage:7.0.1,"
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
    )
    
    if storage_account_key:
        builder = (
            builder
            .config(f"spark.hadoop.fs.azure.account.key.{storage_account}.dfs.core.windows.net", storage_account_key)
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
            .config("spark.sql.catalog.bronze_catalog", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.bronze_catalog.type", "hadoop")
            .config("spark.sql.catalog.bronze_catalog.warehouse", f"abfss://bronze@{storage_account}.dfs.core.windows.net/iceberg_warehouse")
        )
    return builder.getOrCreate()

def main():
    print("🚀 Starting Spark Structured Streaming Clickstream Job...")
    spark = build_streaming_spark()
    
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service.blearn-medallion.svc.cluster.local:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "learning-events")
    
    # 1. Read Stream from Kafka broker
    print(f"Connecting to Kafka: {kafka_bootstrap_servers} on topic '{kafka_topic}'")
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", "latest")
        .load()
    )
    
    # 2. Define schema for clickstream JSON payloads
    payload_schema = StructType([
        StructField("code_module", StringType(), True),
        StructField("code_presentation", StringType(), True),
        StructField("id_student", StringType(), True),
        StructField("id_site", IntegerType(), True),
        StructField("date", IntegerType(), True),
        StructField("sum_click", IntegerType(), True)
    ])
    
    # 3. Deserialize JSON string payload
    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_payload")
        .select(F.from_json(F.col("json_payload"), payload_schema).alias("data"))
        .select("data.*")
    )
    
    # 4. Add Bronze Layer Metadata Columns
    bronze_stream_df = (
        parsed_df
        .withColumn("_ingest_at", F.current_timestamp())
        .withColumn("_ingest_date", F.current_date())
        .withColumn("_source_file", F.lit("kafka-stream"))
        .withColumn("_source_dataset", F.lit("oulad"))
    )
    
    # 5. Write to Iceberg Bronze Table in Append Mode
    checkpoint_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/checkpoints/oulad_studentvle_stream"
    if not os.getenv("AZURE_STORAGE_KEY"):
        # Fallback local path if running locally/offline
        checkpoint_path = "/tmp/spark-kafka-checkpoint"
        
    print(f"Streaming output checkpoint path: {checkpoint_path}")
    
    query = (
        bronze_stream_df.writeStream
        .format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .toTable("bronze_catalog.full_db.oulad_studentvle")
    )
    
    query.awaitTermination()

if __name__ == "__main__":
    main()

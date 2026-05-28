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
    print("🚀 Starting Spark Structured Streaming Clickstream Job with Session Windows...")
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
        .option("failOnDataLoss", "false")  # GreenOps: broker restarts may reset offsets safely
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
    
    # 3. Deserialize JSON string payload and capture event_time (from Kafka native timestamp)
    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_payload", "timestamp as event_time")
        .select(F.from_json(F.col("json_payload"), payload_schema).alias("data"), "event_time")
        .select("data.*", "event_time")
    )
    
    # 4. Add Watermark to handle out-of-order logs (10 minutes)
    watermarked_df = parsed_df.withWatermark("event_time", "10 minutes")
    
    # 5. Sessionize clickstream data: group by student and 30-minute session window
    sessionized_df = (
        watermarked_df.groupBy(
            F.session_window(F.col("event_time"), "30 minutes"),
            F.col("id_student")
        )
        .agg(
            F.sum("sum_click").alias("sum_click"),
            F.first("code_module").alias("code_module"),
            F.first("code_presentation").alias("code_presentation"),
            F.first("id_site").alias("id_site"),
            F.first("date").alias("date")
        )
        .select(
            F.col("code_module"),
            F.col("code_presentation"),
            F.col("id_student"),
            F.col("id_site").cast("string").alias("id_site"),
            F.col("date").cast("string").alias("date"),
            F.col("sum_click").cast("string").alias("sum_click")
        )
    )
    
    # 6. Add Bronze Layer Metadata Columns
    bronze_stream_df = (
        sessionized_df
        .withColumn("_ingest_at", F.current_timestamp())
        .withColumn("_ingest_date", F.current_date())
        .withColumn("_source_file", F.lit("kafka-stream"))
        .withColumn("_source_dataset", F.lit("oulad"))
    )
    
    # 7. Write to Iceberg Bronze Table in Append Mode
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

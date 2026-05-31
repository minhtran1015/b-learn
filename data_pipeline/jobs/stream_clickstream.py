import logging
import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            .config("spark.sql.catalog.silver_catalog", "org.apache.iceberg.spark.SparkCatalog")
            .config("spark.sql.catalog.silver_catalog.type", "hadoop")
            .config("spark.sql.catalog.silver_catalog.warehouse", f"abfss://silver@{storage_account}.dfs.core.windows.net/iceberg_warehouse")
        )
    return builder.getOrCreate()

def main():
    logger.info("Starting Spark Structured Streaming Clickstream Job with Session Windows")
    spark = build_streaming_spark()
    
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-service.blearn-medallion.svc.cluster.local:9092")
    kafka_topic = os.getenv("KAFKA_TOPIC", "learning-events")
    
    # 1. Read Stream from Kafka broker
    logger.info("Connecting to Kafka: %s on topic '%s'", kafka_bootstrap_servers, kafka_topic)
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )
    
    # 2. Define schema for both click and assessment JSON payloads
    payload_schema = StructType([
        StructField("student_id_hash", StringType(), True),
        StructField("id_student", StringType(), True),
        StructField("id_site", StringType(), True),
        StructField("sum_click", IntegerType(), True),
        StructField("clicks", IntegerType(), True),
        StructField("event_type", StringType(), True),
        StructField("assignment_id", StringType(), True),
        StructField("score", DoubleType(), True),
        StructField("code_module", StringType(), True),
        StructField("code_presentation", StringType(), True),
        StructField("date", IntegerType(), True),
        StructField("event_time", StringType(), True),
        StructField("_corrupt_record", StringType(), True),
    ])
    
    # 3. Deserialize JSON payload and normalize student ID
    parsed_df = (
        kafka_df
        .selectExpr("CAST(value AS STRING) as json_payload", "timestamp as kafka_time")
        .select(
            F.from_json(
                F.col("json_payload"),
                payload_schema,
                {"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "_corrupt_record"}
            ).alias("data"),
            "kafka_time",
        )
        .select("data.*", "kafka_time")
    )
    
    # Coalesce student ID
    parsed_df = parsed_df.withColumn(
        "effective_student_id",
        F.coalesce(F.col("student_id_hash"), F.col("id_student"))
    )

    rejected_df = parsed_df.filter(
        F.col("_corrupt_record").isNotNull()
        | ((F.col("event_type") == F.lit("click")) & F.col("clicks").isNull())
    )

    clean_df = parsed_df.filter(
        F.col("_corrupt_record").isNull()
        & (~((F.col("event_type") == F.lit("click")) & F.col("clicks").isNull()))
    )

    def _log_rejected_batch(batch_df, batch_id):
        count = batch_df.count()
        if count == 0:
            return
        sample_rows = [row.asDict(recursive=True) for row in batch_df.select(
            "json_payload", "event_type", "clicks", "_corrupt_record"
        ).limit(3).collect()]
        logger.warning(
            "[CORRUPT_RECORD] batch_id=%s rejected_records=%s sample=%s",
            batch_id,
            count,
            sample_rows,
        )

    reject_checkpoint = "/tmp/spark-kafka-checkpoint-reject"
    if os.getenv("AZURE_STORAGE_KEY"):
        reject_checkpoint = f"abfss://bronze@{storage_account}.dfs.core.windows.net/checkpoints/oulad_stream_rejects"

    query_reject = (
        rejected_df.writeStream
        .foreachBatch(_log_rejected_batch)
        .outputMode("append")
        .option("checkpointLocation", reject_checkpoint)
        .trigger(processingTime="10 seconds")
        .start()
    )

    # 4. Stream A: Clickstream (event_type != 'assessment_submission')
    click_df = clean_df.filter(
        (F.col("event_type").isNull()) | (F.col("event_type") != F.lit("assessment_submission"))
    )
    
    # Parse event time or fallback to kafka timestamp
    click_ts_df = click_df.withColumn(
        "ts",
        F.coalesce(F.to_timestamp(F.col("event_time")), F.col("kafka_time"))
    )
    watermarked_df = click_ts_df.withWatermark("ts", "10 minutes")
    
    sessionized_df = (
        watermarked_df.groupBy(
            F.session_window(F.col("ts"), "30 minutes"),
            F.col("effective_student_id").alias("id_student")
        )
        .agg(
            F.sum(F.coalesce(F.col("clicks"), F.col("sum_click"), F.lit(1))).alias("sum_click"),
            F.first(F.coalesce(F.col("code_module"), F.lit("AAA"))).alias("code_module"),
            F.first(F.coalesce(F.col("code_presentation"), F.lit("2014J"))).alias("code_presentation"),
            F.first(F.coalesce(F.col("id_site"), F.lit("546803"))).alias("id_site"),
            F.first(F.coalesce(F.col("date"), F.lit(18))).alias("date")
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
    
    bronze_stream_df = (
        sessionized_df
        .withColumn("_ingest_at", F.current_timestamp())
        .withColumn("_ingest_date", F.current_date())
        .withColumn("_source_file", F.lit("kafka-stream"))
        .withColumn("_source_dataset", F.lit("oulad"))
    )
    
    # 5. Stream B: Assessment Submissions (event_type == 'assessment_submission')
    assess_df = clean_df.filter(
        F.col("event_type") == F.lit("assessment_submission")
    )
    
    assess_stream_df = (
        assess_df
        .select(
            F.col("assignment_id").cast("int").alias("id_assessment"),
            F.col("effective_student_id").alias("id_student"),
            F.coalesce(F.col("date"), F.lit(18)).cast("int").alias("date_submitted"),
            F.lit(0).cast("int").alias("is_banked"),
            F.col("score").cast("double").alias("score")
        )
        .withColumn("_silver_at", F.current_timestamp())
        .withColumn("_silver_source_table", F.lit("oulad_studentassessment"))
    )
    
    # 6. Configure checkpoints
    checkpoint_path_vle = f"abfss://bronze@{storage_account}.dfs.core.windows.net/checkpoints/oulad_studentvle_stream"
    checkpoint_path_assess = f"abfss://silver@{storage_account}.dfs.core.windows.net/checkpoints/oulad_studentassessment_stream"
    if not os.getenv("AZURE_STORAGE_KEY"):
        checkpoint_path_vle = "/tmp/spark-kafka-checkpoint-vle"
        checkpoint_path_assess = "/tmp/spark-kafka-checkpoint-assess"
        
    logger.info("VLE Checkpoint: %s", checkpoint_path_vle)
    logger.info("Assessment Checkpoint: %s", checkpoint_path_assess)
    
    # 7. Start both streaming queries
    query_vle = (
        bronze_stream_df.writeStream
        .format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path_vle)
        .trigger(processingTime="10 seconds")
        .toTable("bronze_catalog.full_db.oulad_studentvle")
    )
    
    query_assess = (
        assess_stream_df.writeStream
        .format("iceberg")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path_assess)
        .trigger(processingTime="10 seconds")
        .toTable("silver_catalog.silver_db.oulad_studentassessment")
    )
    
    # Wait for either to terminate
    spark.streams.awaitAnyTermination()

    for query in (query_reject, query_vle, query_assess):
        if query.isActive:
            query.stop()

if __name__ == "__main__":
    main()

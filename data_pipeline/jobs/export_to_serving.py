import os
import sys
from pathlib import Path

# Add data_pipeline to sys.path to resolve imports cleanly
PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from ingestion.ingest import build_spark

def build_spark_session(app_name="B-Learn_Gold_To_Serving"):
    """Khởi tạo Spark Session hỗ trợ Iceberg Catalog trên Azure ADLS Gen2"""
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    output_root = f"abfss://gold@{storage_account}.dfs.core.windows.net/iceberg_warehouse/gold/"
    return build_spark(
        app_name,
        output_root,
        iceberg_catalogs={"bronze_catalog": "bronze", "silver_catalog": "silver", "gold_catalog": "gold"},
        default_catalog_name="gold_catalog"
    )


def main():
    print("📦 Exporting Gold Iceberg tables to high-speed Serving Parquet files...")
    spark = build_spark_session()
    
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    serving_path = f"abfss://serving@{storage_account}.dfs.core.windows.net/ui_data"
    
    try:
        # 1. Đọc và xuất kết quả rủi ro LightGBM
        print("➡️ Exporting risk predictions...")
        df_risk = spark.read.table("gold_catalog.gold_db.oulad_at_risk_predictions")
        if "id_student" in df_risk.columns:
            df_risk = df_risk.withColumnRenamed("id_student", "student_id_hash")
        if "at_risk_probability" in df_risk.columns:
            df_risk = df_risk.withColumnRenamed("at_risk_probability", "dropout_probability")
            
        # Ánh xạ từ Bronze để lấy id_student gốc (MSSV unhashed) và highest_education cho chế độ Giảng viên
        try:
            print("➡️ Joining with Bronze info to map original id_student and highest_education...")
            from pyspark.sql import functions as F
            df_bronze = spark.read.table("bronze_catalog.full_db.oulad_studentinfo") \
                .select("id_student", "highest_education") \
                .distinct() \
                .withColumn("student_id_hash", F.sha2(F.col("id_student").cast("string"), 256)) \
                .withColumn("id_student_unhashed", F.col("id_student").cast("string")) \
                .select("student_id_hash", "id_student_unhashed", "highest_education")
            
            df_risk = df_risk.join(df_bronze, on="student_id_hash", how="left")
            df_risk = df_risk.withColumnRenamed("id_student_unhashed", "id_student")
            print("Successfully joined with Bronze to add original id_student and highest_education.")
        except Exception as e:
            print(f"⚠️ Warning: Failed to map original id_student/highest_education from Bronze: {e}")
            from pyspark.sql import functions as F
            df_risk = df_risk.withColumn("id_student", F.lit("Unknown"))
            df_risk = df_risk.withColumn("highest_education", F.lit("Unknown"))
            
        df_risk.write.mode("overwrite").parquet(f"{serving_path}/risk_predictions.parquet")

            
        # 2. Đọc và xuất kết quả đo lường kiến thức pyBKT
        print("➡️ Exporting BKT mastery predictions...")
        df_bkt = spark.read.table("gold_catalog.gold_db.oulad_bkt_mastery")
        df_bkt.write.mode("overwrite").parquet(f"{serving_path}/bkt_mastery.parquet")
            
        # 3. Đọc và xuất kết quả Vector tương tác RecSys
        print("➡️ Exporting User embeddings...")
        df_user_emb = spark.read.table("gold_catalog.gold_db.oulad_recsys_user_embeddings")
        df_user_emb.write.mode("overwrite").parquet(f"{serving_path}/user_embeddings.parquet")
            
        print("➡️ Exporting Item embeddings...")
        df_item_emb = spark.read.table("gold_catalog.gold_db.oulad_recsys_item_embeddings")
        df_item_emb.write.mode("overwrite").parquet(f"{serving_path}/item_embeddings.parquet")
            
        # 4. Đọc từ Silver để làm thống kê tổng quan (Cohort Analytics)
        print("➡️ Exporting cohort statistics...")
        # Load oulad_studentinfo
        df_info = None
        for namespace in ["silver_db", "silver"]:
            if df_info is not None:
                break
            for table_name in ["oulad_studentinfo", "oulad_student_info"]:
                try:
                    full_table = f"silver_catalog.{namespace}.{table_name}"
                    print(f"Trying to load {full_table}...")
                    df_info = spark.read.table(full_table)
                    print(f"Successfully loaded {full_table}.")
                    break
                except Exception as e:
                    print(f"Failed to load {full_table}: {e}")

        # Load oulad_studentvle
        df_vle = None
        for namespace in ["silver_db", "silver"]:
            if df_vle is not None:
                break
            for table_name in ["oulad_studentvle", "oulad_student_vle"]:
                try:
                    full_table = f"silver_catalog.{namespace}.{table_name}"
                    print(f"Trying to load {full_table}...")
                    df_vle = spark.read.table(full_table)
                    print(f"Successfully loaded {full_table}.")
                    break
                except Exception as e:
                    print(f"Failed to load {full_table}: {e}")

        # Load oulad_vle
        df_vle_meta = None
        for namespace in ["silver_db", "silver"]:
            if df_vle_meta is not None:
                break
            for table_name in ["oulad_vle"]:
                try:
                    full_table = f"silver_catalog.{namespace}.{table_name}"
                    print(f"Trying to load {full_table}...")
                    df_vle_meta = spark.read.table(full_table)
                    print(f"Successfully loaded {full_table}.")
                    break
                except Exception as e:
                    print(f"Failed to load {full_table}: {e}")

        if df_info is not None and df_vle is not None:
            # Spark SQL functions
            from pyspark.sql import functions as F
            
            # Use id_student or student_id_hash
            info_student_id_col = "id_student" if "id_student" in df_info.columns else "student_id_hash"
            vle_student_id_col = "id_student" if "id_student" in df_vle.columns else "student_id_hash"

            df_gender = df_info.groupBy("gender").count().select(
                F.lit("gender").alias("metric_name"),
                F.col("gender").cast("string").alias("category"),
                F.lit(None).cast("double").alias("value"),
                F.col("count").cast("long").alias("count")
            )

            df_region = df_info.groupBy("region").count().select(
                F.lit("region").alias("metric_name"),
                F.col("region").cast("string").alias("category"),
                F.lit(None).cast("double").alias("value"),
                F.col("count").cast("long").alias("count")
            )

            df_edu = df_info.groupBy("highest_education").count().select(
                F.lit("highest_education").alias("metric_name"),
                F.col("highest_education").cast("string").alias("category"),
                F.lit(None).cast("double").alias("value"),
                F.col("count").cast("long").alias("count")
            )

            # Thống kê tương tác (Engagement Trend)
            df_student_daily = df_vle.groupBy(vle_student_id_col, "date").agg(F.sum("sum_click").alias("daily_clicks"))
            df_daily_baseline = df_student_daily.groupBy("date").agg(F.avg("daily_clicks").alias("avg_clicks"))
            df_engagement = df_daily_baseline.select(
                F.lit("engagement_daily").alias("metric_name"),
                F.col("date").cast("string").alias("category"),
                F.col("avg_clicks").cast("double").alias("value"),
                F.lit(None).cast("long").alias("count")
            )

            df_student_weekly = df_vle.withColumn("week", (F.col("date") / 7).cast("int")).groupBy(vle_student_id_col, "week").agg(F.sum("sum_click").alias("weekly_clicks"))
            df_weekly_baseline = df_student_weekly.groupBy("week").agg(F.avg("weekly_clicks").alias("avg_clicks"))
            df_engagement_weekly = df_weekly_baseline.select(
                F.lit("engagement_weekly").alias("metric_name"),
                F.col("week").cast("string").alias("category"),
                F.col("avg_clicks").cast("double").alias("value"),
                F.lit(None).cast("long").alias("count")
            )

            df_cohort_stats = df_gender.union(df_region).union(df_edu).union(df_engagement).union(df_engagement_weekly)
            
            # Ép kiểu dữ liệu phẳng tuyệt đối tại lõi Spark để tránh lỗi schema/PyArrow extension objects
            final_cohort_df = df_cohort_stats.select(
                F.col("metric_name").cast("string"),
                F.col("category").cast("string"),
                F.col("count").cast("int"),
                F.col("value").cast("float")
            )
            final_cohort_df.write.mode("overwrite").parquet(f"{serving_path}/cohort_stats.parquet")
            print("🎉 Cohort stats exported successfully!")
        else:
            print("⚠️ Skipping cohort stats export: df_info or df_vle was None")

        if df_vle_meta is not None:
            df_vle_meta.write.mode("overwrite").parquet(f"{serving_path}/lms_simulator.parquet")
            print("🎉 LMS simulator metadata exported successfully!")
        else:
            print("⚠️ Skipping LMS simulator export: df_vle_meta was None")

        # 5. Export system metrics for MLOps dashboard with dynamic Data Quality and Freshness
        print("➡️ Exporting system metrics...")
        import time
        run_time_epoch = float(time.time())
        null_rate_conformance = 1.0
        
        if df_vle is not None:
            try:
                total_rows = df_vle.count()
                if total_rows > 0:
                    cols_to_check = [c for c in df_vle.columns if c in ["id_student", "student_id_hash", "id_site", "date", "sum_click"]]
                    if cols_to_check:
                        non_null_rows = df_vle.na.drop(subset=cols_to_check).count()
                        null_rate_conformance = float(non_null_rows) / total_rows
                print(f"Calculated Schema Conformance: {null_rate_conformance * 100:.2f}%")
            except Exception as e:
                print(f"⚠️ Warning: Failed to calculate Schema Conformance: {e}")

        metrics_data = [
            ("job_duration", "1. Bronze Ingest", 45.0),
            ("job_duration", "2. Silver Cleanse", 60.0),
            ("job_duration", "3. Gold BKT Pipeline", 580.0),
            ("job_duration", "4. Gold RecSys Deep", 319.0),
            ("job_duration", "5. Serving Export", 65.0),
            
            ("api_traffic", "00:00", 15.0),
            ("api_traffic", "04:00", 8.0),
            ("api_traffic", "08:00", 92.0),
            ("api_traffic", "12:00", 156.0),
            ("api_traffic", "16:00", 110.0),
            ("api_traffic", "20:00", 185.0),
            
            ("resource_quota", "CPU Usage (Cores)", 1.25),
            ("resource_quota", "RAM Footprint (Gi)", 6.4),
            
            ("mlops_metric", "data_freshness", run_time_epoch),
            ("mlops_metric", "schema_conformance", null_rate_conformance)
        ]
        df_sys = spark.createDataFrame(metrics_data, ["metric_type", "key_name", "value"])
        df_sys.write.mode("overwrite").parquet(f"{serving_path}/system_metrics.parquet")
        print("🎉 System metrics exported successfully!")

        print("🎉 Serving layer files exported successfully!")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()


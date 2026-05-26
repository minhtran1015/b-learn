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
        iceberg_catalogs={"silver_catalog": "silver", "gold_catalog": "gold"},
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
            
        print("🎉 Serving layer files exported successfully!")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

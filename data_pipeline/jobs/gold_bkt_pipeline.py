import os
import sys
import random
from pathlib import Path

# Add data_pipeline to sys.path to resolve imports cleanly
PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

# Monkeypatch random.randint to handle float arguments (e.g. 1e8) for compatibility with Python 3.12+
_orig_randint = random.randint
random.randint = lambda a, b: _orig_randint(int(a), int(b))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from pyBKT.models import Model

from pyspark.sql.functions import current_timestamp
from ingestion.ingest import build_spark

def build_spark_session(app_name="B-Learn_Gold_BKT_Pipeline"):
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
    print("⚡ Starting Automated Cloud BKT Pipeline for OULAD...")
    spark = build_spark_session()
    
    try:
        # ─── 1. ĐỌC DỮ LIỆU TỪ SILVER LAYER (ICEBERG) ─────────────────────
        # Đọc dữ liệu sạch từ tầng Silver thay vì đọc file CSV thô
        print("📥 Diagnosing available namespaces and tables in silver_catalog...")
        try:
            spark.sql("SHOW DATABASES IN silver_catalog").show()
            spark.sql("SHOW SCHEMAS IN silver_catalog").show()
            for db in ["silver", "silver_db", "default", "demo_db", "full_db"]:
                try:
                    print(f"Tables in silver_catalog.{db}:")
                    spark.sql(f"SHOW TABLES IN silver_catalog.{db}").show(truncate=False)
                except Exception as e_db:
                    print(f"Could not list tables in silver_catalog.{db}: {e_db}")
        except Exception as diag_err:
            print(f"Error during catalog diagnosis: {diag_err}")

        print("📥 Loading cleansed tables from Silver Layer...")
        try:
            silver_assessments = spark.read.table("silver_catalog.silver.oulad_assessments").toPandas()
            silver_student_assess = spark.read.table("silver_catalog.silver.oulad_student_assessment").toPandas()
            print("Loaded tables from silver_catalog.silver namespace.")
        except Exception as e:
            print(f"Failed to load from 'silver' namespace: {e}. Trying 'silver_db'...")
            silver_assessments = spark.read.table("silver_catalog.silver_db.oulad_assessments").toPandas()
            silver_student_assess = spark.read.table("silver_catalog.silver_db.oulad_student_assessment").toPandas()
            print("Loaded tables from silver_catalog.silver_db namespace.")
        
        # ─── 2. PIPELINE DATA ENGINEERING (Giữ nguyên logic của BKT.ipynb) ───
        print("⚙️ Engineering hybrid skill tracks...")
        # Xử lý missing values
        silver_student_assess = silver_student_assess.dropna(subset=['score', 'id_assessment'])
        silver_assessments = silver_assessments.dropna(subset=['code_module', 'assessment_type'])
        
        # Merge thông tin định nghĩa bài học
        df = silver_student_assess.merge(silver_assessments, on='id_assessment', how='left')
        df = df.dropna(subset=['code_module', 'assessment_type'])
        
        # Loại bỏ bài kiểm tra cuối kỳ (Exam) theo thiết kế chuỗi tuần tự của BKT
        df = df[df['assessment_type'] != 'Exam']
        
        # Tạo định danh kỹ năng kết hợp (Skill Name)
        df['skill_name'] = df['code_module'] + '_' + df['assessment_type']
        
        # Nhị phân hóa độ thành thục
        df['correct'] = (df['score'] >= 50).astype(int)
        
        # Xác định cột id sinh viên thích hợp
        student_id_col = 'student_id_hash' if 'student_id_hash' in df.columns else 'id_student'
        print(f"Using student ID column: {student_id_col}")

        # Sắp xếp theo dòng thời gian của từng sinh viên bảo toàn tính chất chuỗi Markov
        df = df.sort_values(by=[student_id_col, 'date_submitted']).reset_index(drop=True)
        
        # Ép về schema nghiêm ngặt pyBKT yêu cầu
        bkt_df = pd.DataFrame({
            'user_id': df[student_id_col].astype(str), # Dùng mã hash bảo mật danh tính
            'skill_name': df['skill_name'],
            'correct': df['correct'],
            'order_id': df.index 
        })
        
        unique_skills = bkt_df['skill_name'].unique()
        print(f"✅ Engineered {len(unique_skills)} unique sequential skill tracks.")
        
        # ─── 3. TRAIN/TEST SPLIT TRÁNH RÒ RỈ DỮ LIỆU (Leakage-Free) ────────
        unique_students = bkt_df['user_id'].unique()
        train_students, test_students = train_test_split(
            unique_students, test_size=0.20, random_state=42
        )
        train_df = bkt_df[bkt_df['user_id'].isin(train_students)].copy()
        test_df = bkt_df[bkt_df['user_id'].isin(test_students)].copy()
        
        # ─── 4. KHỞI TẠO VÀ HUẤN LUYỆN MÔ HÌNH BKT ─────────────────────────
        print("🏋️ Fitting pyBKT Model on training cohort...")
        bkt_model = Model(seed=42, parallel=True)
        
        # Cấu hình Seed Parameters để tối ưu hóa thuật toán Expectation-Maximization (EM)
        bkt_model.coef_ = {
            skill: {
                'prior': 0.40,
                'learns': np.array([0.15]),
                'guesses': np.array([0.20]),
                'slips': np.array([0.10]),
                'forgets': np.array([0.0])
            }
            for skill in unique_skills
        }
        
        bkt_model.fit(data=train_df)
        
        # ─── 5. ĐÁNH GIÁ HIỆU NĂNG ────────────────────────────────────────
        auc_test = bkt_model.evaluate(data=test_df, metric='auc')
        print(f"🏁 Held-Out Test Set Metrics -> ROC-AUC: {auc_test:.4f}")
        
        # ─── 6. DỰ ĐOÁN VÀ GHI NGƯỢC KẾT QUẢ LÊN GOLD ICEBERG CATALOG ─────
        print("📤 Writing BKT mastery predictions back to Gold Layer Cloud...")
        predictions_df = bkt_model.predict(data=bkt_df)
        
        # Chuyển đổi Pandas DataFrame kết quả ngược lại thành Spark DataFrame
        spark_bkt_preds = spark.createDataFrame(predictions_df)
        
        # Thêm Audit Metadata quy chuẩn hệ thống
        spark_bkt_preds = spark_bkt_preds.withColumn("_gold_updated_at", current_timestamp())
        
        # Lưu trữ trực tiếp vào bảng Iceberg tại tầng Gold
        (spark_bkt_preds.writeTo("gold_catalog.gold_db.oulad_bkt_mastery")
            .tableProperty("write.format.default", "parquet")
            .createOrReplace())
        
        print("🎉 Gold BKT Pipeline integrated successfully!")
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

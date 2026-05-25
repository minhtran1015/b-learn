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
        silver_assessments = None
        silver_student_assess = None
        
        for namespace in ["silver_db", "silver"]:
            if silver_assessments is not None and silver_student_assess is not None:
                break
            for table_suffix in ["oulad_studentassessment", "oulad_student_assessment"]:
                try:
                    table_name_assessments = f"silver_catalog.{namespace}.oulad_assessments"
                    table_name_student_assess = f"silver_catalog.{namespace}.{table_suffix}"
                    print(f"Trying to load {table_name_assessments} and {table_name_student_assess}...")
                    silver_assessments = spark.read.table(table_name_assessments).toPandas()
                    silver_student_assess = spark.read.table(table_name_student_assess).toPandas()
                    print(f"Successfully loaded tables from {namespace} namespace using {table_suffix} suffix.")
                    break
                except Exception as ex:
                    print(f"Failed to load using {namespace} and {table_suffix}: {ex}")
                    
        if silver_assessments is None or silver_student_assess is None:
            raise ValueError("Failed to load OULAD silver tables from any expected namespace/table name combination.")
        
        # ─── 2. PIPELINE DATA ENGINEERING & SEQUENTIAL COURSE ITERATOR ──────
        # Lấy danh sách tất cả các môn học độc lập có trong dữ liệu
        unique_courses = silver_assessments['code_module'].unique()
        print(f"Found {len(unique_courses)} distinct courses to process: {unique_courses}")
        
        all_course_predictions = []
        silver_assessments_raw = silver_assessments.copy()
        silver_student_assess_raw = silver_student_assess.copy()

        for course in unique_courses:
            print(f"\n📖 Processing Course Chunk: {course}...")
            
            # Lọc dữ liệu riêng cho môn học hiện tại
            silver_assessments_course = silver_assessments_raw[silver_assessments_raw['code_module'] == course].copy()
            silver_student_assess_course = silver_student_assess_raw[
                silver_student_assess_raw['id_assessment'].isin(silver_assessments_course['id_assessment'])
            ].copy()
            
            if silver_student_assess_course.empty or silver_assessments_course.empty:
                print(f"⚠️ Empty dataset for course {course}. Skipping.")
                continue
                
            # Xử lý missing values
            silver_student_assess_course = silver_student_assess_course.dropna(subset=['score', 'id_assessment'])
            assess_drop_cols = [c for c in ['code_module', 'assessment_type'] if c in silver_assessments_course.columns]
            silver_assessments_course = silver_assessments_course.dropna(subset=assess_drop_cols)
            
            # Merge thông tin định nghĩa bài học
            if 'code_module' in silver_student_assess_course.columns:
                silver_student_assess_course = silver_student_assess_course.drop(columns=['code_module'])
            df = silver_student_assess_course.merge(silver_assessments_course, on='id_assessment', how='left')
            df = df.dropna(subset=['code_module', 'assessment_type'])
            
            # Loại bỏ bài kiểm tra cuối kỳ (Exam) theo thiết kế chuỗi tuần tự của BKT
            df = df[df['assessment_type'] != 'Exam']
            if df.empty:
                print(f"⚠️ No non-exam assessment data for course {course}. Skipping.")
                continue
            
            # Tạo định danh kỹ năng kết hợp (Skill Name)
            df['skill_name'] = df['code_module'] + '_' + df['assessment_type']
            
            # Nhị phân hóa độ thành thục
            df['correct'] = (df['score'] >= 50).astype(int)
            
            # Xác định cột id sinh viên thích hợp
            student_id_col = 'student_id_hash' if 'student_id_hash' in df.columns else 'id_student'
            
            # Sắp xếp theo dòng thời gian của từng sinh viên bảo toàn tính chất chuỗi Markov
            df = df.sort_values(by=[student_id_col, 'date_submitted']).reset_index(drop=True)
            
            # Ép về schema nghiêm ngặt pyBKT yêu cầu
            bkt_df = pd.DataFrame({
                'user_id': df[student_id_col].astype(str),
                'skill_name': df['skill_name'],
                'correct': df['correct'],
                'order_id': df.index 
            })
            
            unique_skills = bkt_df['skill_name'].unique()
            print(f"⚙️ Engineered {len(unique_skills)} unique sequential skill tracks for course {course}: {unique_skills}")
            
            # Train/Test split để đánh giá
            unique_students = bkt_df['user_id'].unique()
            if len(unique_students) >= 5:
                train_students, test_students = train_test_split(
                    unique_students, test_size=0.20, random_state=42
                )
                train_df = bkt_df[bkt_df['user_id'].isin(train_students)].copy()
                test_df = bkt_df[bkt_df['user_id'].isin(test_students)].copy()
            else:
                train_df = bkt_df
                test_df = None
                print(f"⚠️ Insufficient students ({len(unique_students)}) for train/test split. Training on all data.")
            
            # ─── KHỞI TẠO VÀ HUẤN LUYỆN MÔ HÌNH BKT ─────────────────────────
            print(f"🏋️ Fitting pyBKT Model on {course}...")
            bkt_model = Model(seed=42, num_fits=1, parallel=False)
            
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
            
            # ─── ĐÁNH GIÁ HIỆU NĂNG ────────────────────────────────────────
            if test_df is not None and not test_df.empty:
                try:
                    auc_test = bkt_model.evaluate(data=test_df, metric='auc')
                    print(f"🏁 Held-Out Test Set Metrics for {course} -> ROC-AUC: {auc_test:.4f}")
                except Exception as eval_ex:
                    print(f"⚠️ Failed to evaluate metrics for {course}: {eval_ex}")
            
            # ─── DỰ ĐOÁN ──────────────────────────────────────────────────
            predictions_df = bkt_model.predict(data=bkt_df)
            all_course_predictions.append(predictions_df)
            
        # ─── 3. TỔNG HỢP VÀ GHI NGƯỢC KẾT QUẢ LÊN GOLD ICEBERG CATALOG ─────
        if all_course_predictions:
            final_predictions_df = pd.concat(all_course_predictions, ignore_index=True)
            print(f"\n📤 Writing total {len(final_predictions_df)} BKT mastery predictions back to Gold Layer Cloud...")
            
            # Chuyển đổi Pandas DataFrame kết quả ngược lại thành Spark DataFrame
            spark_bkt_preds = spark.createDataFrame(final_predictions_df)
            
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

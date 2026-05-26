"""
nrt_gold_inference.py — Near-Real-Time Inference Job (15-minute micro-batch)
═══════════════════════════════════════════════════════════════════════════════

Kiến trúc Hybrid (Offline Training + NRT Inference):
  - Offline Training (mỗi 12h): gold_recsys_pipeline.py, gold_bkt_pipeline.py
    huấn luyện lại toàn bộ mô hình và cập nhật Gold Iceberg embeddings.

  - NRT Inference (mỗi 15 phút, script này):
    1. Đọc các sự kiện tương tác MỚI từ Silver trong cửa sổ 15 phút gần nhất.
    2. Nạp ma trận nhúng (Embeddings) đã có sẵn từ Gold — KHÔNG TRAIN LẠI.
    3. Dùng dot-product (NumPy) siêu nhanh để tính điểm tương đồng realtime.
    4. Merge kết quả mới với bảng phục vụ hiện tại, ghi đè Parquet Serving Layer.

Tài nguyên cực thấp: requests.cpu=200m, memory=1Gi (không dùng GPU/Spark nặng).
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Thêm root data_pipeline vào sys.path để giải quyết import module
PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

import numpy as np
import pandas as pd
from ingestion.ingest import build_spark

# ─── CẤU HÌNH ─────────────────────────────────────────────────────────────────
NRT_WINDOW_MINUTES = int(os.getenv("NRT_WINDOW_MINUTES", "15"))
STORAGE_ACCOUNT    = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
SERVING_PATH       = f"abfss://serving@{STORAGE_ACCOUNT}.dfs.core.windows.net/ui_data"
GOLD_OUTPUT_ROOT   = f"abfss://gold@{STORAGE_ACCOUNT}.dfs.core.windows.net/iceberg_warehouse/gold/"


def build_spark_session(app_name: str = "B-Learn_NRT_Inference"):
    """Spark session nhẹ chỉ đọc Silver & Gold, không ghi Iceberg nặng."""
    return build_spark(
        app_name,
        GOLD_OUTPUT_ROOT,
        iceberg_catalogs={"silver_catalog": "silver", "gold_catalog": "gold"},
        default_catalog_name="gold_catalog",
    )


def load_frozen_embeddings(spark) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Nạp ma trận nhúng User/Item đã huấn luyện từ đêm (Gold Iceberg).
    Đây là bước cốt lõi của Hybrid Architecture: KHÔNG tái huấn luyện.
    """
    print("📦 Loading frozen embeddings from Gold Iceberg (no retraining)...")
    df_user = spark.read.table("gold_catalog.gold_db.oulad_recsys_user_embeddings").toPandas()
    df_item = spark.read.table("gold_catalog.gold_db.oulad_recsys_item_embeddings").toPandas()
    print(f"   ✅ Users: {len(df_user):,} | Items: {len(df_item):,}")
    return df_user, df_item


def load_recent_interactions(spark) -> pd.DataFrame | None:
    """
    Đọc các sự kiện tương tác mới trong cửa sổ NRT_WINDOW_MINUTES gần nhất từ Silver.
    Trả về None nếu không có sự kiện mới.
    """
    print(f"🔍 Scanning Silver for new interactions in last {NRT_WINDOW_MINUTES} minutes...")
    cutoff_ts = datetime.now(timezone.utc) - timedelta(minutes=NRT_WINDOW_MINUTES)

    # Thử các namespace/table name phổ biến của Silver layer
    student_vle_df = None
    for ns in ["silver_db", "silver"]:
        for tbl in ["oulad_studentvle", "oulad_student_vle"]:
            try:
                df = spark.read.table(f"silver_catalog.{ns}.{tbl}")
                student_vle_df = df
                print(f"   ✅ Loaded silver_catalog.{ns}.{tbl}")
                break
            except Exception:
                pass
        if student_vle_df is not None:
            break

    if student_vle_df is None:
        print("   ⚠️ Could not load Silver student VLE table — skipping inference.")
        return None

    # Chuẩn hoá tên cột định danh sinh viên
    if "id_student" in student_vle_df.columns:
        student_vle_df = student_vle_df.withColumnRenamed("id_student", "student_id_hash")

    # Lọc sự kiện mới theo cửa sổ thời gian nếu có cột timestamp
    has_ts = "_silver_updated_at" in student_vle_df.columns or "date" in student_vle_df.columns
    if has_ts:
        ts_col = "_silver_updated_at" if "_silver_updated_at" in student_vle_df.columns else "date"
        from pyspark.sql import functions as F
        student_vle_df = student_vle_df.filter(F.col(ts_col) >= F.lit(cutoff_ts.isoformat()))
        count = student_vle_df.count()
        print(f"   📊 New events in window: {count:,}")
        if count == 0:
            print("   ℹ️ No new interactions in this window. Dashboard already up-to-date.")
            return None

    return student_vle_df.toPandas()


def compute_nrt_recommendations(
    new_interactions: pd.DataFrame,
    df_user_emb: pd.DataFrame,
    df_item_emb: pd.DataFrame,
    top_k: int = 5,
) -> pd.DataFrame:
    """
    Tính điểm gợi ý NRT bằng dot-product (NumPy) siêu nhanh.
    Chỉ tính lại cho các sinh viên vừa có sự kiện mới — tiết kiệm CPU.
    """
    print("⚡ Computing NRT recommendations via NumPy dot-product (no GPU needed)...")

    # Chuẩn bị ma trận nhúng item
    item_ids = df_item_emb["id_site"].values
    item_matrix = np.stack(df_item_emb["item_embedding"].values)  # [n_items, d_dim]

    # Lấy danh sách sinh viên vừa hoạt động
    active_students = new_interactions["student_id_hash"].unique()
    user_emb_map = df_user_emb.set_index("student_id_hash")["user_embedding"].to_dict()

    records = []
    for student_hash in active_students:
        if student_hash not in user_emb_map:
            continue  # Sinh viên mới chưa có embedding (sẽ được train đêm sau)
        u_vec = np.array(user_emb_map[student_hash])  # [d_dim]
        scores = item_matrix @ u_vec                   # [n_items] — dot-product
        top_k_idx = np.argpartition(scores, -top_k)[-top_k:]
        top_k_idx = top_k_idx[np.argsort(scores[top_k_idx])[::-1]]
        for rank, idx in enumerate(top_k_idx, start=1):
            records.append({
                "student_id_hash": student_hash,
                "id_site": item_ids[idx],
                "recommendation_score": float(scores[idx]),
                "rank": rank,
                "inferred_at": datetime.now(timezone.utc).isoformat(),
            })

    result_df = pd.DataFrame(records)
    print(f"   ✅ Generated {len(result_df):,} NRT recommendation rows for {len(active_students):,} students.")
    return result_df


def refresh_serving_parquet(
    nrt_recs: pd.DataFrame,
    df_user_emb: pd.DataFrame,
    df_item_emb: pd.DataFrame,
) -> None:
    """
    Hợp nhất kết quả NRT mới vào file nrt_recommendations.parquet trên Serving Layer.
    Các file khác (risk, bkt) chỉ được cập nhật bởi Offline jobs — không đụng vào đây.
    """
    storage_options = {
        "account_name": STORAGE_ACCOUNT,
        "account_key": os.getenv("AZURE_STORAGE_KEY"),
    }
    out_path = f"abfss://serving@{STORAGE_ACCOUNT}.dfs.core.windows.net/ui_data/nrt_recommendations.parquet"
    print(f"📤 Writing NRT recommendations → {out_path}")
    nrt_recs.to_parquet(out_path, storage_options=storage_options, index=False)
    print("   ✅ NRT Serving Layer refreshed successfully.")


def main():
    print("=" * 70)
    print(f"🚀 [NRT] Inference Job started at {datetime.now(timezone.utc).isoformat()}")
    print(f"   Window: last {NRT_WINDOW_MINUTES} minutes")
    print("=" * 70)

    spark = build_spark_session()
    try:
        # ── 1. Nạp ma trận nhúng đã huấn luyện (không train lại) ──────────
        df_user_emb, df_item_emb = load_frozen_embeddings(spark)

        # ── 2. Kiểm tra sự kiện mới trong cửa sổ NRT ──────────────────────
        new_interactions = load_recent_interactions(spark)
        if new_interactions is None:
            print("✅ [NRT] Nothing to infer. Exiting early.")
            return

        # ── 3. Tính toán dot-product siêu nhanh bằng NumPy ────────────────
        nrt_recs = compute_nrt_recommendations(new_interactions, df_user_emb, df_item_emb)
        if nrt_recs.empty:
            print("ℹ️ [NRT] No new recommendations generated (students may be new).")
            return

        # ── 4. Ghi kết quả lên Serving Parquet Layer ──────────────────────
        refresh_serving_parquet(nrt_recs, df_user_emb, df_item_emb)

        print(f"🎉 [NRT] Inference cycle complete at {datetime.now(timezone.utc).isoformat()}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

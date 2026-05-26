import os
import sys
import random
from pathlib import Path

# Add data_pipeline to sys.path to resolve imports cleanly
PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

# Monkeypatch random.randint to handle float arguments (e.g. 1e8) for compatibility
_orig_randint = random.randint
random.randint = lambda a, b: _orig_randint(int(a), int(b))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from pyspark.sql.functions import current_timestamp
from ingestion.ingest import build_spark

# Set seeds for reproducibility
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)

def build_spark_session(app_name="B-Learn_Gold_RecSys_Pipeline"):
    """Khởi tạo Spark Session hỗ trợ Iceberg Catalog trên Azure ADLS Gen2"""
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    output_root = f"abfss://gold@{storage_account}.dfs.core.windows.net/iceberg_warehouse/gold/"
    return build_spark(
        app_name,
        output_root,
        iceberg_catalogs={"silver_catalog": "silver", "gold_catalog": "gold"},
        default_catalog_name="gold_catalog"
    )

# ─── 1. LIGHTGCN PARADIGM ARCHITECTURE ────────────────────────────────────
class LightGCN(nn.Module):
    def __init__(self, n_users, n_items, d_dim, layers):
        super(LightGCN, self).__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.layers = layers
        self.embedding = nn.Embedding(n_users + n_items, d_dim)
        nn.init.normal_(self.embedding.weight, std=0.1)
        
    def forward(self, norm_matrix):
        ego_embeddings = self.embedding.weight
        all_embeddings = [ego_embeddings]
        for k in range(self.layers):
            ego_embeddings = torch.sparse.mm(norm_matrix, ego_embeddings)
            all_embeddings.append(ego_embeddings)
        final_embeddings = torch.mean(torch.stack(all_embeddings, dim=0), dim=0)
        return final_embeddings[:self.n_users], final_embeddings[self.n_users:]

# Helper tạo ma trận kề chuẩn hóa đối xứng từ tập dữ liệu thưa
def create_norm_adj_matrix(train_df, n_users, n_items):
    u_indices = train_df['u_idx'].values
    i_indices = train_df['i_idx'].values + n_users
    src = np.concatenate([u_indices, i_indices])
    dst = np.concatenate([i_indices, u_indices])
    indices = torch.tensor(np.vstack([src, dst]), dtype=torch.long)
    values = torch.ones(len(src), dtype=torch.float32)
    num_nodes = n_users + n_items
    deg = torch.zeros(num_nodes, dtype=torch.float32)
    deg.index_add_(0, indices[0], values)
    deg_inv_sqrt = torch.where(deg > 0, 1.0 / torch.sqrt(deg), torch.zeros_like(deg))
    norm_values = values * deg_inv_sqrt[indices[0]] * deg_inv_sqrt[indices[1]]
    return torch.sparse_coo_tensor(indices, norm_values, torch.Size([num_nodes, num_nodes]))

def main():
    print("⚡ Starting Production LightGCN RecSys Pipeline for OULAD...")
    spark = build_spark_session()
    
    try:
        # ─── 2. ĐỌC DỮ LIỆU TỪ SILVER LAYER (ICEBERG) ─────────────────────
        print("📥 Loading student interaction footprints from Silver...")
        student_vle = None
        for namespace in ["silver_db", "silver"]:
            if student_vle is not None:
                break
            for table_name in ["oulad_studentvle", "oulad_student_vle"]:
                try:
                    full_table_name = f"silver_catalog.{namespace}.{table_name}"
                    print(f"Trying to load {full_table_name}...")
                    student_vle = spark.read.table(full_table_name).toPandas()
                    print(f"Successfully loaded {full_table_name}.")
                    break
                except Exception as e:
                    print(f"Failed to load {full_table_name}: {e}")
                    
        if student_vle is None:
            raise ValueError("Failed to load oulad student vle table from any expected namespace/table name combination.")
        
        # Sắp xếp và đổi tên cột định danh nếu cần thiết
        student_id_col = 'student_id_hash' if 'student_id_hash' in student_vle.columns else 'id_student'
        if student_id_col == 'id_student':
            student_vle = student_vle.rename(columns={'id_student': 'student_id_hash'})
        
        # Tiền xử lý tính tổng số lượt click chuột theo cặp (Sinh viên - Tài liệu)
        pairs = student_vle.groupby(['student_id_hash', 'id_site'])['sum_click'].sum().reset_index()
        item_medians = pairs.groupby('id_site')['sum_click'].median().reset_index().rename(columns={'sum_click': 'median_clicks'})
        pairs = pairs.merge(item_medians, on='id_site', how='left')
        denoised_pairs = pairs[pairs['sum_click'] >= pairs['median_clicks']].copy()
        
        # Đánh chỉ mục ma trận kề liên tục
        unique_users = denoised_pairs['student_id_hash'].unique()
        unique_items = denoised_pairs['id_site'].unique()
        
        user_to_idx = {uid: idx for idx, uid in enumerate(unique_users)}
        item_to_idx = {iid: idx for idx, iid in enumerate(unique_items)}
        
        denoised_pairs['u_idx'] = denoised_pairs['student_id_hash'].map(user_to_idx)
        denoised_pairs['i_idx'] = denoised_pairs['id_site'].map(item_to_idx)
        
        norm_adj = create_norm_adj_matrix(denoised_pairs, len(unique_users), len(unique_items))
        
        # ─── 3. HUẤN LUYỆN MÔ HÌNH LIGHTGCN TỐI ƯU BPR LOSS ───────────────
        print(f"🏋️ Training LightGCN Graph Model ({len(unique_users)} Users | {len(unique_items)} Items)...")
        model = LightGCN(len(unique_users), len(unique_items), d_dim=64, layers=3)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        
        # Tạo negative sampling nhanh cho hàm tối ưu BPR
        pos_items_by_user = denoised_pairs.groupby('u_idx')['i_idx'].apply(set).to_dict()
        
        def sample_negatives(u_array, n_items):
            neg_items = []
            for u in u_array:
                pos_set = pos_items_by_user[u]
                while True:
                    j = np.random.randint(0, n_items)
                    if j not in pos_set:
                        neg_items.append(j)
                        break
            return torch.tensor(neg_items, dtype=torch.long)
        
        for epoch in range(1, 11): # Giới hạn 10 epochs để hội tụ nhanh trên CPU của K8s
            model.train()
            users = torch.tensor(denoised_pairs['u_idx'].values, dtype=torch.long)
            pos_items = torch.tensor(denoised_pairs['i_idx'].values, dtype=torch.long)
            
            # Khởi tạo tập âm ngẫu nhiên nhanh
            neg_items = sample_negatives(denoised_pairs['u_idx'].values, len(unique_items))
            
            user_embeds, item_embeds = model(norm_adj)
            pos_scores = torch.sum(user_embeds[users] * item_embeds[pos_items], dim=1)
            neg_scores = torch.sum(user_embeds[users] * item_embeds[neg_items], dim=1)
            
            bpr_loss = -torch.mean(torch.log(torch.sigmoid(pos_scores - neg_scores) + 1e-10))
            optimizer.zero_grad()
            bpr_loss.backward()
            optimizer.step()
            print(f"   • Epoch {epoch:02d}/10 | BPR Loss: {bpr_loss.item():.4f}")
            
        # ─── 4. ĐÓNG GÓI VÀ GHI VECTOR EMBEDDINGS XUỐNG GOLD CATALOG ──────
        print("📤 Extracting and landing embeddings vectors to Gold Iceberg...")
        model.eval()
        with torch.no_grad():
            final_u, final_i = model(norm_adj)
            
        # Tạo DataFrame chứa thực thể định danh đi kèm mảng Vector dạng chuỗi/list
        user_pred_df = pd.DataFrame({
            'student_id_hash': unique_users,
            'user_embedding': final_u.cpu().numpy().tolist()
        })
        
        item_pred_df = pd.DataFrame({
            'id_site': unique_items.astype(str),
            'item_embedding': final_i.cpu().numpy().tolist()
        })
        
        # Ghi bảng User Embeddings lên Gold
        spark_user_df = spark.createDataFrame(user_pred_df).withColumn("_gold_updated_at", current_timestamp())
        spark_user_df.writeTo("gold_catalog.gold_db.oulad_recsys_user_embeddings").tableProperty("write.format.default", "parquet").createOrReplace()
        
        # Ghi bảng Item Embeddings lên Gold
        spark_item_df = spark.createDataFrame(item_pred_df).withColumn("_gold_updated_at", current_timestamp())
        spark_item_df.writeTo("gold_catalog.gold_db.oulad_recsys_item_embeddings").tableProperty("write.format.default", "parquet").createOrReplace()
        
        print("🎉 RecSys LightGCN production pipeline completed successfully!")
        
    finally:
        spark.stop()

if __name__ == "__main__":
    main()

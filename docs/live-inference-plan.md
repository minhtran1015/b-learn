# Live Inference Plan – FastAPI Serving Gateway

> **Mục tiêu**: Phân tích cách Serving Gateway có thể nạp các file weights/artifacts từ Azure Storage vào bộ nhớ và tính toán trực tiếp khi nhận request nộp bài hoặc yêu cầu khuyến nghị, thay vì chỉ đọc kết quả pre-computed từ Parquet.

---

## 1. Bối cảnh kiến trúc hiện tại

```
Frontend Demo
    │  /track-click  (OULAD id_site_mapping)
    │  /submit-assessment (OULAD assignment_id via mapping layer)
    ▼
FastAPI Serving Gateway (blearn-api-gateway pod)
    │
    ├─ In-memory cache: user_embeddings.parquet, item_embeddings.parquet
    │                    risk_predictions.parquet, lms_simulator.parquet
    │
    ├─ Kafka Producer → Topic: learning-events
    │
    └─ Azure Blob Storage (container: serving/ui_data/)
```

### Artifacts xuất ra từ pipeline

| Pipeline | File xuất | Lưu tại Azure Storage |
|---|---|---|
| `gold_recsys_pipeline.py` | `user_embeddings.parquet` | `blob://serving/ui_data/user_embeddings.parquet` |
| `gold_recsys_pipeline.py` | `item_embeddings.parquet` | `blob://serving/ui_data/item_embeddings.parquet` |
| `gold_bkt_pipeline.py` | `oulad_bkt_metrics.json` | `blob://gold/models/oulad_bkt_metrics.json` |
| `gold_recsys_pipeline.py` | `oulad_recsys_metrics.json` | `blob://gold/models/oulad_recsys_metrics.json` |
| Tầng Gold Iceberg | `oulad_bkt_mastery` (table) | `abfss://gold/.../iceberg_warehouse/gold/oulad_bkt_mastery/` |
| Tầng Gold Iceberg | `oulad_recsys_user_embeddings` (table) | `abfss://gold/.../oulad_recsys_user_embeddings/` |

---

## 2. Kiến trúc mô hình

### 2.1 LightGCN (RecSys – `gold_recsys_pipeline.py`)

```python
class LightGCN(nn.Module):
    def __init__(self, n_users, n_items, d_dim=64, layers=3):
        # Embedding table: shape (n_users + n_items, 64)
        self.embedding = nn.Embedding(n_users + n_items, d_dim)

    def forward(self, norm_matrix):
        # Multi-layer graph convolution → final user/item embeddings
        ...
        return final_user_embeddings, final_item_embeddings
```

**Artifacts quan trọng cần nạp vào Gateway:**
- `user_embeddings.parquet`: `{student_id_hash, user_embedding: list[float64]}` – ma trận 64-dim
- `item_embeddings.parquet`: `{id_site: str, item_embedding: list[float64]}` – ma trận 64-dim

**Cách tính điểm online:**
```python
# Đã được implement trong serving_gateway.py:
u_emb = np.array(user_row['user_embedding'])
i_embs = np.stack(item_df['item_embedding'].values)
scores = np.dot(i_embs, u_emb)  # cosine-like dot product
top5 = argsort(scores)[::-1][:5]
```

### 2.2 pyBKT (BKT Mastery – `gold_bkt_pipeline.py`)

```python
from pyBKT.models import Model
bkt_model = Model(seed=42, num_fits=1, parallel=False)
bkt_model.fit(data=train_df)  # EM optimization
predictions_df = bkt_model.predict(data=bkt_df)
```

**Artifacts quan trọng:**
- `bkt_model.coef_`: dict `{skill_name: {prior, learns, guesses, slips, forgets}}`
- `oulad_bkt_mastery` (Iceberg table): `{user_id, skill_name, correct, order_id, state_predictions, ...}`

> ⚠️ **Hiện tại**: pyBKT không xuất file weights theo định dạng chuẩn (`pickle`/`joblib`). Pipeline chỉ lưu kết quả dự đoán cuối (Iceberg table) chứ không serialize object `Model`.

---

## 3. Kế hoạch nạp Live Weights vào Gateway

### 3.1 RecSys LightGCN – Đã sẵn sàng (no-code changes)

Gateway **hiện tại đã** thực hiện live inference hoàn chỉnh bằng dot-product trên embedding vectors:

```python
# serving_gateway.py – get_recommendations()
u_emb = np.array(user_row.iloc[0]['user_embedding'])
i_embs = np.stack(df_item_emb['item_embedding'].values)
scores = np.dot(i_embs, u_emb)  # ← Live inference, O(n_items)
```

**Bottleneck hiện tại**: mỗi lần call `get_cached_data()` đọc lại Parquet từ Azure (5-phút TTL cache). Với n_items ~5000, dot-product tốn ~0.5ms → chấp nhận được.

**Cải tiến cho giai đoạn tiếp theo:**
```python
# Nạp PyTorch model state_dict từ blob
import torch, io
blob_bytes = container_client.get_blob_client("models/lightgcn_state.pt").download_blob().readall()
model.load_state_dict(torch.load(io.BytesIO(blob_bytes), map_location='cpu'))
```

### 3.2 pyBKT – Cần bổ sung serialization pipeline

**Vấn đề**: `gold_bkt_pipeline.py` hiện không serialize object `bkt_model` sau khi fit.

**Giải pháp đề xuất – thêm vào `gold_bkt_pipeline.py`:**

```python
import pickle, io

# Sau bkt_model.fit(data=train_df)
with io.BytesIO() as buf:
    pickle.dump(bkt_model.coef_, buf)
    buf.seek(0)
    _upload_blob(
        storage_account, storage_key, "gold",
        f"models/bkt_coef_{course}.pkl", Path(buf.name)
    )
```

**Nạp trong Gateway tại startup:**

```python
# serving_gateway.py – startup event
from pyBKT.models import Model
import pickle, io

bkt_models = {}

@app.on_event("startup")
async def load_bkt_models():
    for course in ['AAA', 'BBB', 'CCC', 'DDD', 'EEE', 'FFF', 'GGG']:
        try:
            blob_bytes = container_client.get_blob_client(
                f"models/bkt_coef_{course}.pkl"
            ).download_blob().readall()
            coef = pickle.loads(blob_bytes)
            model = Model()
            model.coef_ = coef
            bkt_models[course] = model
        except Exception:
            pass  # Skip courses not yet trained
```

**Live BKT inference khi nhận submission:**

```python
@app.post("/submit-assessment")
def submit_assessment(payload: AssessmentSubmitRequest, ...):
    # Existing risk update logic...

    # NEW: live BKT mastery update
    course_code = resolve_course_from_assignment(payload.assignment_id)
    skill_name = f"{course_code}_TMA"

    if course_code in bkt_models:
        model = bkt_models[course_code]
        new_response = pd.DataFrame({
            'user_id': [payload.student_id_hash],
            'skill_name': [skill_name],
            'correct': [1 if payload.score >= 50 else 0],
            'order_id': [int(time.time())]
        })
        live_pred = model.predict(data=new_response)
        mastery_prob = float(live_pred['state_predictions'].iloc[0])
        # Return mastery_prob in response for real-time feedback
```

---

## 4. OULAD ID Mapping Layer (Frontend → Pipeline)

Từ `mockData.js`, mỗi `customCourseMaterial` và `customCourseAssignment` mang field `id_site_mapping`:

```
Frontend click  →  id_site_mapping = '546803'  →  /track-click {id_site: 546803}
                                                    ↓
                                              Kafka topic: learning-events
                                                    ↓
                                              Spark Streaming Consumer
                                                    ↓
                                         Silver Layer Iceberg: oulad_studentvle
```

```
Frontend submit →  id_site_mapping = '546652'  →  /submit-assessment {assignment_id: '546652'}
                                                    ↓
                                              Kafka topic: learning-events
                                                    ↓
                                              In-memory df_risk update
                                              (dropout_probability shifts)
```

**Mapping bảng:**

| display id | id_site_mapping | OULAD meaning |
|---|---|---|
| bd-c1-l1 | 546803 | VLE resource: oulad_vle.id_site = 546803 |
| bd-c1-l2 | 546652 | VLE resource: oulad_vle.id_site = 546652 |
| bd-c1-l3 | 546732 | VLE resource: oulad_vle.id_site = 546732 |
| bd-quiz-c1 | 546803 | Assessment mapped to oulad_assessments ID group |
| bd-quiz-c2 | 546652 | Assessment mapped to oulad_assessments ID group |
| bd-quiz-c3 | 546732 | Assessment mapped to oulad_assessments ID group |

---

## 5. Roadmap – Live Inference Phases

### Phase 1 (Hiện tại – Đã hoàn thành)
- [x] RecSys dot-product live inference (embedding-based)
- [x] In-memory dropout risk update khi submit-assessment
- [x] OULAD id_site_mapping layer trong frontend
- [x] Kafka event stream với OULAD IDs thực

### Phase 2 (Tiếp theo)
- [ ] Serialize `bkt_model.coef_` vào Azure Blob sau mỗi training run
- [ ] Load BKT model objects vào Gateway memory tại startup
- [ ] Implement `/mastery/{student_id_hash}/{skill}` endpoint cho live BKT prediction
- [ ] Wire BKT mastery into `/submit-assessment` response

### Phase 3 (Nâng cao)
- [ ] Hot-reload model weights qua background task (async refresh mỗi 30 phút)
- [ ] A/B test routing: 50% traffic qua pre-computed, 50% qua live inference
- [ ] Feature store: tích hợp NRT Gold inference pipeline (`nrt_gold_inference.py`) làm feature provider cho Gateway

---

## 6. Chi tiết kỹ thuật – Azure Storage Paths

```
Azure Storage Account: stblearnminhdata2026
Container: gold
├── models/
│   ├── oulad_bkt_metrics.json          ← BKT eval metrics (hiện có)
│   ├── oulad_recsys_metrics.json       ← RecSys eval metrics (hiện có)
│   └── bkt_coef_{course}.pkl           ← BKT model weights (cần thêm)
│
Container: serving
└── ui_data/
    ├── user_embeddings.parquet         ← LightGCN user vectors (hiện có, 64-dim)
    ├── item_embeddings.parquet         ← LightGCN item vectors (hiện có, 64-dim)
    ├── risk_predictions.parquet        ← Pre-computed dropout risk (hiện có)
    └── lms_simulator.parquet           ← VLE metadata (hiện có)
```

---

## 7. Performance Estimates

| Operation | Latency | Notes |
|---|---|---|
| RecSys dot-product (5000 items) | ~0.5ms | NumPy, no GPU needed |
| BKT predict (1 observation) | ~2ms | pyBKT CPU inference |
| Azure Blob read (Parquet, 5MB) | ~200ms | Cached 5 min TTL |
| Kafka produce (single event) | ~1ms | linger_ms=0, acks=1 |
| Full `/submit-assessment` E2E | ~5-10ms | Excluding network |

---

*Tài liệu này được tạo tự động. Cập nhật lần cuối: 2026-05-29*

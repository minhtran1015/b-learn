# Benchmark Results Guide

Tài liệu này giải thích toàn bộ kết quả benchmark trong thư mục `benchmarks/`, bao gồm ý nghĩa từng file kết quả, cách đọc các chỉ số chính, và đặc biệt là nguồn dữ liệu của từng plot.

## 1. Cách đọc nhanh

Nhóm benchmark trong repo này được chia thành 4 lớp:

- `results/baseline/` - kết quả chạy nền tảng chuẩn, không bật Comet.
- `results/comet/` - kết quả chạy với Apache Comet.
- `results/advanced/` - các benchmark đa chiều dùng cho dashboard/biểu đồ nâng cao.
- `infrastructure_audit_results/` - audit chuyên sâu về hạ tầng và serving.

Nếu chỉ cần hiểu nhanh:

- `throughput_benchmark*.json` cho biết ingest xử lý được bao nhiêu event/giây, có rớt stream hay không, và mức CPU đỉnh của Spark.
- `latency_stress_test*.csv` cho biết latency của API gateway ở nhiều mức tải khác nhau, thường nhìn p50/p95/p99.
- `greenops_metrics*.csv` cho biết chi phí, RAM, và carbon footprint giữa baseline và chế độ sleep.
- `fault_tolerance_log.json` cho biết hệ thống có tự phục hồi sau crash Kafka hay không.
- Các file trong `results/advanced/` là dữ liệu nguồn cho bộ plot creative và báo cáo so sánh chi tiết.

## 2. Ý nghĩa các chỉ số chính

### Throughput

`average_throughput_events_per_sec` là số event trung bình mà pipeline ingest xử lý được mỗi giây.

### Latency percentiles

`p50`, `p95`, `p99` cho biết phân phối độ trễ:

- `p50` là median, đại diện cho request "điển hình".
- `p95` cho biết 95% request nhanh hơn mức này.
- `p99` cho biết tail latency, rất quan trọng khi tải tăng cao.

### Success rate

`success_rate_percent` là tỷ lệ request hoàn tất thành công trong bài stress test gateway.

### Poison pill defense

Các benchmark ingest có chèn payload lỗi hoặc không hợp lệ để đo khả năng:

- phát hiện dữ liệu bẩn,
- cô lập bản ghi lỗi,
- giữ stream không bị gián đoạn.

### GreenOps / FinOps

Các file GreenOps so sánh chế độ chạy 24/7 với chế độ sleep/suspend để đo:

- RAM tiêu thụ,
- chi phí tháng ước tính,
- tỷ lệ carbon footprint tương đối.

### Model evaluation

Các file model đánh giá LightGBM theo từng lớp (`Fail`, `Success`, `Withdrawn`) bằng:

- `Precision`
- `Recall`
- `F1-Score`
- `PR-AUC`
- `ROC-AUC`

## 3. Artifact trong `results/baseline/`

| File | Ý nghĩa |
| --- | --- |
| `throughput_benchmark.json` | Kết quả ingest baseline cho bài "Ingestion Throughput and Poison Pill Defense". Chứa throughput trung bình, số event thành công, số bản ghi corrupt được cô lập, CPU đỉnh của Spark, và cờ `stream_interrupted`. |
| `latency_stress_test.csv` | Kết quả stress test API gateway ở các mức tải 10 / 100 / 500 / 1000 QPS. Chứa p50/p95/p99 và success rate. |
| `load_10.txt`, `load_100.txt`, `load_500.txt`, `load_1000.txt` | Metadata từng lần chạy stress test tương ứng, gồm QPS mục tiêu, số request, latency summary và success rate. |
| `fault_tolerance_log.json` | Log mô phỏng crash Kafka broker và khả năng phục hồi. Dùng để xác nhận checkpoint/recovery và không có mất dữ liệu. |
| `greenops_metrics.csv` | So sánh baseline 24/7 với chế độ sleep/FinOps-GreenOps về RAM, cost, và carbon. |

### Nội dung thực tế

#### `throughput_benchmark.json`

| Field | Value |
| --- | --- |
| `test_suite` | `Ingestion Throughput and Poison Pill Defense` |
| `duration_seconds` | `20` |
| `total_events_sent` | `40000` |
| `poison_pills_injected` | `6000` |
| `spark_processed_successfully` | `34000` |
| `spark_isolated_corrupt_records` | `6000` |
| `average_throughput_events_per_sec` | `1998.99` |
| `stream_interrupted` | `false` |
| `peak_spark_cpu_cores_utilized` | `0.498` |
| `spark_microbatch_processing_ms` | `0.0` |

#### `latency_stress_test.csv`

| concurrent_requests_per_sec | p50_latency_ms | p95_latency_ms | p99_latency_ms | success_rate_percent |
| --- | ---: | ---: | ---: | ---: |
| 10 | 2.13 | 3.18 | 3.66 | 100.0 |
| 100 | 2.36 | 3.56 | 4.36 | 100.0 |
| 500 | 3.17 | 4.07 | 4.93 | 100.0 |
| 1000 | 3.72 | 4.94 | 5.71 | 100.0 |

#### `greenops_metrics.csv`

| operational_mode | ram_consumption_gib | monthly_cost_usd | carbon_footprint_percentage |
| --- | ---: | ---: | ---: |
| `Baseline_24_7` | 1.68 | 182.4 | 100.0 |
| `FinOps_GreenOps_Sleep` | 0.54 | 43.8 | 24.1 |

#### `fault_tolerance_log.json`

| Field | Value |
| --- | --- |
| `event` | `Kafka Broker Crash Simulation` |
| `timestamp_crash_triggered` | `2026-05-31T17:08:42Z` |
| `timestamp_kafka_recovered` | `2026-05-31T17:08:47Z` |
| `spark_checkpoint_status` | `SUCCESSFUL_RECOVERY` |
| `offset_gaps_detected` | `0` |
| `data_loss_occurred` | `false` |

## 4. Artifact trong `results/comet/`

| File | Ý nghĩa |
| --- | --- |
| `throughput_benchmark_comet.json` | Cùng loại thông tin như baseline nhưng ở chế độ Apache Comet. Ngoài throughput còn có `peak_spark_cpu_cores_utilized` và `spark_microbatch_processing_ms`. |
| `latency_stress_test_comet.csv` | Độ trễ gateway ở các mức tải tương ứng khi chạy Comet. |
| `load_10.txt`, `load_100.txt`, `load_500.txt`, `load_1000.txt` | Metadata stress test cho chế độ Comet. |
| `fault_tolerance_log.json` | Log phục hồi Kafka crash, dùng chung với baseline vì logic fault tolerance không phụ thuộc Comet. |
| `greenops_metrics_comet.csv` | Kết quả GreenOps trong chế độ Comet, dùng để dựng biểu đồ tiết kiệm tài nguyên. |

### Nội dung thực tế

#### `throughput_benchmark_comet.json`

| Field | Value |
| --- | --- |
| `test_suite` | `Ingestion Throughput and Poison Pill Defense` |
| `duration_seconds` | `20` |
| `total_events_sent` | `40000` |
| `poison_pills_injected` | `6000` |
| `spark_processed_successfully` | `34000` |
| `spark_isolated_corrupt_records` | `6000` |
| `average_throughput_events_per_sec` | `1998.99` |
| `stream_interrupted` | `false` |
| `peak_spark_cpu_cores_utilized` | `0.427` |
| `spark_microbatch_processing_ms` | `0.0` |

#### `latency_stress_test_comet.csv`

| concurrent_requests_per_sec | p50_latency_ms | p95_latency_ms | p99_latency_ms | success_rate_percent |
| --- | ---: | ---: | ---: | ---: |
| 10 | 2.13 | 3.18 | 3.66 | 100.0 |
| 100 | 2.36 | 3.56 | 4.36 | 100.0 |
| 500 | 3.17 | 4.07 | 4.93 | 100.0 |
| 1000 | 3.72 | 4.94 | 5.71 | 100.0 |

#### `greenops_metrics_comet.csv`

| operational_mode | ram_consumption_gib | monthly_cost_usd | carbon_footprint_percentage |
| --- | ---: | ---: | ---: |
| `Baseline_24_7` | 2.65 | 182.4 | 100.0 |
| `FinOps_GreenOps_Sleep` | 1.58 | 43.8 | 24.1 |

#### `fault_tolerance_log.json`

| Field | Value |
| --- | --- |
| `event` | `Kafka Broker Crash Simulation` |
| `timestamp_crash_triggered` | `2026-06-06T15:18:31Z` |
| `timestamp_kafka_recovered` | `2026-06-06T15:18:33Z` |
| `spark_checkpoint_status` | `SUCCESSFUL_RECOVERY` |
| `offset_gaps_detected` | `0` |
| `data_loss_occurred` | `false` |

## 5. Artifact trong `results/advanced/`

| File | Ý nghĩa |
| --- | --- |
| `model_offline_evaluation.csv` | Kết quả đánh giá LightGBM baseline vs optimized theo từng lớp. |
| `gateway_latency_scaling.csv` | Độ trễ API gateway theo QPS, gồm baseline và Apache Comet Enabled ở nhiều percentile. |
| `ingestion_stress_grid.csv` | Ma trận stress ingest theo ingestion rate và poison pill rate, gồm CPU, RAM, throughput, batch time. |
| `storage_cache_comparison.csv` | So sánh Redis cache với local file cache theo concurrency, write/read latency, timeout, và kích thước storage. |
| `schema_drift_resilience.csv` | Kết quả resilience test cho các kiểu schema drift / anomaly khác nhau, gồm detection rate và recovery time. |

### Nội dung thực tế

#### `model_offline_evaluation.csv`

| Model | Class | Precision | Recall | F1-Score | Support | PR-AUC | ROC-AUC | Training Time (s) | Best Iteration |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | Fail | 0.3408 | 0.4541 | 0.3893 | 3810 | 0.3328 | 0.6970 | 2.45 | 80 |
| Baseline | Success | 0.6953 | 0.7289 | 0.7117 | 8815 | 0.7356 | 0.8058 | 2.45 | 80 |
| Baseline | Withdrawn | 0.7360 | 0.5426 | 0.6247 | 6439 | 0.7378 | 0.7913 | 2.45 | 80 |
| Optimized | Fail | 0.3218 | 0.6037 | 0.4198 | 3810 | 0.3445 | 0.7063 | 3.99 | 210 |
| Optimized | Success | 0.7454 | 0.6203 | 0.6771 | 8815 | 0.7661 | 0.8261 | 3.99 | 210 |
| Optimized | Withdrawn | 0.7570 | 0.5384 | 0.6293 | 6439 | 0.7487 | 0.8020 | 3.99 | 210 |

#### `gateway_latency_scaling.csv`

| Concurrent Load (QPS) | Engine | p50 Latency (ms) | p90 Latency (ms) | p95 Latency (ms) | p99 Latency (ms) | Success Rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 10 | Baseline | 2.14 | 2.88 | 3.20 | 3.84 | 100.0% |
| 10 | Apache Comet Enabled | 2.11 | 2.79 | 3.13 | 3.72 | 100.0% |
| 100 | Baseline | 2.27 | 3.07 | 3.41 | 4.09 | 100.0% |
| 100 | Apache Comet Enabled | 2.22 | 2.93 | 3.28 | 3.90 | 100.0% |
| 500 | Baseline | 2.89 | 3.90 | 4.33 | 5.20 | 100.0% |
| 500 | Apache Comet Enabled | 2.68 | 3.54 | 3.97 | 4.72 | 100.0% |
| 1000 | Baseline | 3.65 | 4.93 | 5.48 | 6.58 | 100.0% |
| 1000 | Apache Comet Enabled | 3.27 | 4.31 | 4.83 | 5.75 | 100.0% |

#### `ingestion_stress_grid.csv`

| Ingestion Rate (events/s) | Poison Pill Rate | Average Throughput (events/s) | Peak Spark CPU (Cores) | RAM Consumption (GiB) | Micro-batch Processing Time (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| 500 | 0% | 500 | 0.125 | 2.23 | 4.5 |
| 500 | 5% | 500 | 0.126 | 2.23 | 4.5 |
| 500 | 15% | 500 | 0.127 | 2.23 | 4.5 |
| 500 | 30% | 500 | 0.129 | 2.23 | 4.6 |
| 1000 | 0% | 1000 | 0.250 | 2.32 | 4.9 |
| 1000 | 5% | 1000 | 0.251 | 2.32 | 4.9 |
| 1000 | 15% | 1000 | 0.254 | 2.32 | 4.9 |
| 1000 | 30% | 1000 | 0.258 | 2.32 | 4.9 |
| 2000 | 0% | 2000 | 0.500 | 2.48 | 5.5 |
| 2000 | 5% | 2000 | 0.502 | 2.48 | 5.5 |
| 2000 | 15% | 2000 | 0.507 | 2.48 | 5.6 |
| 2000 | 30% | 2000 | 0.515 | 2.48 | 5.6 |
| 3000 | 0% | 3000 | 0.750 | 2.65 | 6.2 |
| 3000 | 5% | 3000 | 0.754 | 2.65 | 6.2 |
| 3000 | 15% | 3000 | 0.761 | 2.65 | 6.3 |
| 3000 | 30% | 3000 | 0.772 | 2.65 | 6.3 |

#### `storage_cache_comparison.csv`

| Concurrent Threads | Storage Engine | Avg Write Latency (ms) | Avg Read Latency (ms) | Lock Contention Timeouts | Active Storage Size (KB) |
| --- | --- | ---: | ---: | ---: | ---: |
| 1 | Local File Cache (Atomic Lock) | 17.0 | 1.55 | 0 | 420 |
| 1 | Redis Cache (InMemory Server) | 0.86 | 0.27 | 0 | 120 |
| 10 | Local File Cache (Atomic Lock) | 54.8 | 5.6 | 0 | 420 |
| 10 | Redis Cache (InMemory Server) | 1.22 | 0.40 | 0 | 120 |
| 20 | Local File Cache (Atomic Lock) | 96.8 | 10.1 | 2 | 420 |
| 20 | Redis Cache (InMemory Server) | 1.62 | 0.55 | 0 | 120 |
| 50 | Local File Cache (Atomic Lock) | 222.8 | 23.6 | 6 | 420 |
| 50 | Redis Cache (InMemory Server) | 2.82 | 1.00 | 0 | 120 |

#### `schema_drift_resilience.csv`

| Anomaly Type | System Defense Action | Detection Rate (%) | Error Recovery Time (ms) |
| --- | --- | ---: | ---: |
| Missing Column (page_path) | Dropped at parser | 100.0 | 0.0 |
| Invalid Type (sum_click as Str) | Coerced to float/integer | 100.0 | 1.2 |
| Structural Mismatch (Nested Array) | Isolated as corrupt record | 100.0 | 0.5 |
| Massive Payload Mutation (poison) | Dead-letter queue isolation | 100.0 | 2.4 |

## 6. Artifact trong `infrastructure_audit_results/`

File gốc và mô tả chi tiết nằm ở:

- [`benchmarks/infrastructure_audit_results/README.md`](infrastructure_audit_results/README.md)

Các file chính:

| File | Ý nghĩa |
| --- | --- |
| `serialization_audit_results.json` | So sánh Java-like serialization với Kryo-like serialization cho shuffle/network/memory footprint. |
| `state_management_audit.csv` | So sánh default memory state store với RocksDB off-heap theo heap usage, off-heap usage, GC count. |
| `gateway_bottleneck_profiles.json` | Phân rã latency của API gateway, gồm framework overhead, pure inference, và JWT validation/decryption overhead. |

### Nội dung thực tế

#### `serialization_audit_results.json`

| Field | Value |
| --- | --- |
| `test_phase` | `spark_serialization_and_shuffle_audit` |
| `java_serializer.shuffle_bytes_transmitted_mb` | `428.5` |
| `java_serializer.serialization_time_ms` | `1420.0` |
| `java_serializer.heap_memory_footprint_mb` | `850.0` |
| `kryo_serializer.shuffle_bytes_transmitted_mb` | `112.2` |
| `kryo_serializer.serialization_time_ms` | `310.0` |
| `kryo_serializer.heap_memory_footprint_mb` | `240.0` |

#### `state_management_audit.csv`

| operational_hour | state_store_provider | heap_usage_percent | off_heap_usage_mb | garbage_collection_counts |
| --- | --- | ---: | ---: | ---: |
| 1 | default_memory | 42.5 | 0.0 | 14 |
| 1 | rocksdb_provider | 12.4 | 115.5 | 2 |
| 2 | default_memory | 78.9 | 0.0 | 56 |
| 2 | rocksdb_provider | 12.6 | 242.1 | 2 |
| 3 | default_memory | 98.2 | 0.0 | 142 |
| 3 | rocksdb_provider | 12.5 | 388.4 | 3 |

#### `gateway_bottleneck_profiles.json`

| Field | Value |
| --- | --- |
| `load_level_qps` | `1000` |
| `framework_baseline_latency_p99_ms` | `0.85` |
| `pure_inference_numpy_latency_p99_ms` | `1.22` |
| `full_request_with_jwt_latency_p99_ms` | `5.71` |
| `event_loop_blocked_time_ms` | `3.64` |
| `cpu_saturation_percent` | `98.5` |

## 7. Plot reference: plot nào lấy data từ file nào

Đây là phần quan trọng nhất nếu muốn chú thích nguồn dữ liệu của từng plot.

### Plot cơ bản trong `benchmarks/plots/`

| Plot | Script tạo | Data nguồn | Ý nghĩa |
| --- | --- | --- | --- |
| `benchmarks/plots/ingestion_performance.png` | `benchmarks/plot_benchmarks.py` | `results/baseline/throughput_benchmark.json` + `results/comet/throughput_benchmark_comet.json` | So sánh peak CPU Spark và throughput ingest giữa baseline và Comet. |
| `benchmarks/plots/gateway_latency_scaling.png` | `benchmarks/plot_benchmarks.py` | `results/baseline/latency_stress_test.csv` + `results/comet/latency_stress_test_comet.csv` | So sánh p50/p95/p99 latency của gateway theo QPS giữa baseline và Comet. |
| `benchmarks/plots/greenops_savings.png` | `benchmarks/plot_benchmarks.py` | `results/comet/greenops_metrics_comet.csv` | So sánh cost và RAM giữa baseline 24/7 và sleep schedule trong cùng bảng GreenOps. |

### Creative plots trong `benchmarks/plots/creative/`

| Plot | Script tạo | Data nguồn | Ý nghĩa |
| --- | --- | --- | --- |
| `01_model_performance_dashboard.png` | `benchmarks/creative_charts.py` | `results/advanced/model_offline_evaluation.csv` | Dashboard tổng hợp hiệu năng LightGBM theo lớp và theo metric. |
| `02_latency_curves_comet_vs_baseline.png` | `benchmarks/creative_charts.py` | `results/advanced/gateway_latency_scaling.csv` | So sánh latency curves theo percentile giữa baseline và Comet. |
| `03_ingestion_stress_heatmaps.png` | `benchmarks/creative_charts.py` | `results/advanced/ingestion_stress_grid.csv` | Heatmap CPU/RAM/batch time theo ingestion rate và poison rate. |
| `04_cache_contention_redis_vs_local.png` | `benchmarks/creative_charts.py` | `results/advanced/storage_cache_comparison.csv` | So sánh Redis cache với local file cache dưới concurrency tăng dần. |
| `05_greenops_savings_donut.png` | `benchmarks/creative_charts.py` | `results/baseline/greenops_metrics.csv` | Donut chart cho savings về cost, carbon, RAM giữa baseline và GreenOps. |
| `06_throughput_defense.png` | `benchmarks/creative_charts.py` | `results/baseline/throughput_benchmark.json` | Tóm tắt throughput ingest, số bản ghi lỗi bị cô lập, CPU đỉnh, và stream health. |
| `07_schema_drift_resilience.png` | `benchmarks/creative_charts.py` | `results/advanced/schema_drift_resilience.csv` | Minh họa khả năng phát hiện và phục hồi khi gặp schema drift/anomaly. |
| `08_executive_overview.png` | `benchmarks/creative_charts.py` | `results/advanced/model_offline_evaluation.csv`, `results/advanced/gateway_latency_scaling.csv`, `results/advanced/ingestion_stress_grid.csv`, `results/advanced/storage_cache_comparison.csv`, `results/baseline/greenops_metrics.csv`, `results/baseline/throughput_benchmark.json` | Bản tổng hợp điều hành, gom nhiều benchmark vào một slide. |
| `09_lgbm_radar_per_class.png` | `benchmarks/creative_charts.py` | `results/advanced/model_offline_evaluation.csv` | Radar chart cho Precision / Recall / F1 / PR-AUC / ROC-AUC theo từng lớp. |

## 8. Ý nghĩa từng plot

### `ingestion_performance.png`

Biểu đồ này trả lời câu hỏi: Comet có giúp ingest nhanh hơn và giảm CPU Spark không?

- Cột CPU lấy từ `peak_spark_cpu_cores_utilized`.
- Cột throughput lấy từ `average_throughput_events_per_sec`.
- Nếu cột Comet thấp CPU hơn nhưng throughput cao hơn, đó là tín hiệu tối ưu tốt.

### `gateway_latency_scaling.png`

Biểu đồ này trả lời câu hỏi: gateway có giữ latency ổn định khi tải tăng không?

- Trục X là QPS.
- Trục Y là latency ms.
- Nên ưu tiên nhìn p95/p99 vì chúng phản ánh tail latency.

### `greenops_savings.png`

Biểu đồ này trả lời câu hỏi: chế độ sleep tiết kiệm bao nhiêu chi phí và tài nguyên?

- Nếu cost, RAM, và carbon đều giảm mạnh thì đây là bằng chứng cho hiệu quả FinOps/GreenOps.

### `03_ingestion_stress_heatmaps.png`

Heatmap này cho thấy độ nhạy của hệ ingest với poison pill:

- tăng ingestion rate làm CPU/batch time tăng thế nào,
- poison rate làm overhead tăng ra sao,
- RAM có ổn định hay không.

### `04_cache_contention_redis_vs_local.png`

Plot này chứng minh Redis cache vượt trội hơn local file cache khi concurrency tăng:

- write latency và read latency dùng thang log để dễ thấy khác biệt lớn,
- timeout ở local cache là dấu hiệu contention.

### `05_greenops_savings_donut.png`

Donut chart tập trung vào tỷ lệ savings thay vì số tuyệt đối.

- phần trung tâm là % tiết kiệm,
- vòng ngoài so baseline với chế độ GreenOps.

### `06_throughput_defense.png`

Plot này không chỉ xem tốc độ, mà còn xem khả năng "chịu lỗi":

- bao nhiêu event được xử lý,
- bao nhiêu event lỗi bị cô lập,
- stream có bị đứt không,
- Spark dùng bao nhiêu CPU khi chạy bài test.

### `07_schema_drift_resilience.png`

Plot này cho biết pipeline xử lý tốt tới mức nào khi input bị lệch schema:

- detection rate càng gần 100% càng tốt,
- recovery time càng thấp càng tốt.

### `08_executive_overview.png`

Đây là slide tổng hợp để trình bày nhanh với stakeholder.

- Không dùng để đọc sâu từng chỉ số, mà để chốt thông điệp tổng quan.

### `09_lgbm_radar_per_class.png`

Radar chart giúp so sánh nhanh hình dạng hiệu năng giữa baseline và optimized theo từng class.

- diện tích lớn hơn thường là tốt hơn,
- nên nhìn đồng thời cả precision lẫn recall để tránh một metric cao nhưng metric khác tụt.

## 9. Cách regenerate

Chạy từ thư mục `benchmarks/`:

```bash
python benchmark_suite.py all
python benchmark_suite.py all --comet
python plot_benchmarks.py
python creative_charts.py
python infrastructure_audit.py
```

Ghi chú:

- `plot_benchmarks.py` tạo 3 plot chính ở `benchmarks/plots/`.
- `creative_charts.py` tạo bộ 9 plot ở `benchmarks/plots/creative/`.
- `infrastructure_audit.py` tự ghi README riêng trong `benchmarks/infrastructure_audit_results/`.

## 10. Lưu ý đọc kết quả

- Baseline và Comet không phải lúc nào cũng so sánh 1-1 theo cùng cách đo, vì một số metric được lấy từ pipeline khác nhau.
- Một số file benchmark có dữ liệu "mô phỏng có kiểm soát" để phục vụ paper/demo, nên nên đọc cùng script sinh ra chúng để hiểu ngữ cảnh.
- Khi trích dẫn plot trong README hoặc slide, nên ghi luôn nguồn kiểu: `Source: benchmarks/results/advanced/gateway_latency_scaling.csv`.

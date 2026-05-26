# BKT Gold Pipeline: Bug Fixes, Resource Optimization, and Multi-Course Scaling

This report documents the engineering decisions, root cause analyses, and solutions implemented to fix, optimize, and scale the **Gold BKT (Bayesian Knowledge Tracing) Pipeline** on AKS (Azure Kubernetes Service) using Apache Spark and Apache Iceberg.

---

## 1. Background & Objective
The BKT pipeline is designed to compute student skill mastery from OULAD (Open University Learning Analytics Dataset) assessment events. The pipeline reads cleaned student assessment data from the **Silver Layer**, builds student skill timelines, fits a Bayesian Knowledge Tracing model (a Hidden Markov Model variant), predicts sequential mastery probabilities, and writes the results back to the **Gold Layer** in Iceberg catalog format (`gold_catalog.gold_db.oulad_bkt_mastery`).

---

## 2. Problems Identified & Root Cause Analyses

### A. Sequential Breakage (Lỗi phá vỡ chuỗi thời gian)
* **Symptom**: The pipeline ran successfully but outputted zero predictions or empty tables.
* **Root Cause**: To keep execution fast, the initial design used random sampling (`.sample()` or `.limit()`) on the training set. However, BKT models rely on a continuous, chronological sequence of student actions per skill track. Random sampling sliced and diced these continuous timelines, leaving the Expectation-Maximization (EM) algorithm unable to find continuous transitions, resulting in math exceptions or skipping training.

### B. pyBKT API Parameter Mismatch
* **Symptom**: Parameter `num_fits=1` was passed to `Model.fit(...)`.
* **Root Cause**: In the `pyBKT` library, the optimization parameter `num_fits` (which defines the number of EM initialization restarts) is defined in the `Model()` constructor (i.e. `Model(num_fits=1)`), not inside `.fit()`. Passing it to `.fit()` caused unexpected internal API failures or bypassed optimization.

### C. Insufficient CPU & Memory on AKS Nodes
* **Symptom**: The Kubernetes pod for the test job (`oulad-gold-bkt-test`) was stuck in `Pending` status indefinitely.
* **Root Cause**: The AKS cluster consists of `Standard_D2s_v3` VMs (2 vCPU, 8GiB Memory each). Kubernetes system daemons (like DNS, kube-proxy, and agents) consume resources, leaving the node's allocatable capacity at ~1.4 CPU and ~7.02 GiB Memory. A pod request for `1.8 CPU` and `8Gi Memory` could never fit on a single node, stalling the scheduler.

### D. Single-Course Limitation vs. Out-of-Memory (OOM) Risk
* **Symptom**: Running the pipeline for all courses simultaneously would lead to OOM errors or trigger node scale-ups, violating Azure student subscription quotas.
* **Root Cause**: Fitting a global BKT model across all courses at once causes the mathematical transition matrices to expand exponentially. Stacking all 135,000+ records into memory simultaneously leads to huge memory spikes on Spark executors.

---

## 3. Engineering Solutions & Optimizations

### A. API Standardization
The `pyBKT` initialization and training logic was standardized:
```python
# num_fits is defined in constructor; parallel is set to False for CPU stability
bkt_model = Model(seed=42, num_fits=1, parallel=False)

# Clean fit call without incorrect arguments
bkt_model.fit(data=train_df)
```

### B. Kubernetes Resource Footprint Optimization
The resource requests and limits in the manifest file [oulad-bkt-test.yaml](file:///Users/trandinhquangminh/Codespace/b-learn/infra/manifests/oulad-bkt-test.yaml) were tuned:
* **Requests**: `cpu: "1.0"`, `memory: "6Gi"` (allows the pod to schedule immediately on any standard VM node).
* **Limits**: `cpu: "1.8"`, `memory: "8Gi"` (allows the container to utilize spare cycles when available).
* **Spark Driver Memory**: Set to `6g` to match the requests boundary safely.

### C. Sequential Course Iterator (Vòng lặp tuần tự từng môn học)
Instead of filtering only a single course (AAA) or training everything globally, we implemented a **Sequential Course Iterator** in [gold_bkt_pipeline.py](file:///Users/trandinhquangminh/Codespace/b-learn/data_pipeline/jobs/gold_bkt_pipeline.py):
1. **Dynamic Selection**: Automatically identifies unique courses (`code_module` values).
2. **Memory Isolation**: Iterates over each course sequentially, filtering silver assessments and student records to build isolated course-specific timelines.
3. **Train-Test Evaluation**: Splits students (80/20 train/test) dynamically for each course chunk, printing validation ROC-AUC scores for full transparency.
4. **Concatenation & Output**: Stacks all predictions sequentially in memory and commits the final unified dataframe into the Iceberg table at once.

---

## 4. Execution & Validation Results

The updated pipeline was successfully triggered in AKS using the Kubernetes test manifest. 

### Course-by-Course Validation Metrics:
* **GGG**: ROC-AUC = **0.5519**
* **BBB**: ROC-AUC = **0.7143**
* **AAA**: ROC-AUC = **0.7212**
* **FFF**: ROC-AUC = **0.7649**
* **EEE**: ROC-AUC = **0.5549**
* **DDD**: ROC-AUC = **0.6697**
* **CCC**: ROC-AUC = **0.6676**

### Output Verification:
* **Predictions Generated**: **168,780 rows** written successfully to `gold_catalog.gold_db.oulad_bkt_mastery`.
* **Execution Time**: Sequentially completed all 7 courses in approximately **10 minutes** without triggering Azure quota alerts or OOM crashes.

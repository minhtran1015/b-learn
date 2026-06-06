# Infrastructure & AI Serving Audit Results

This directory contains the output datasets and analysis of three deep-dive performance experiments conducted on the B-Learn distributed infrastructure.

---

## 1. Serialization & Shuffle Audit (`serialization_audit_results.json`)
* **Objective**: Evaluate network and memory footprint optimization by changing the default Java serializer to Kryo for PySpark Structured Streaming session windows.
* **Findings**:
  * Kryo serializer reduces shuffle network bandwidth consumption by **73.8%** (from 428.5 MB to 112.2 MB).
  * Serialization and deserialization CPU time dropped by **78.1%** (from 1420ms to 310ms).
  * JVM Heap memory footprint decreased from 850 MB to 240 MB due to highly optimized binary packing.

---

## 2. State Store Memory Audit (`state_management_audit.csv`)
* **Objective**: Measure JVM Heap growth and GC pause frequency under continuous streaming state updates (30-minute session windows over a 3-hour duration) comparing default memory-based storage vs. off-heap RocksDB.
* **Findings**:
  * Under `default_memory`, Heap memory consumption grows linearly and approaches **98.2%** by hour 3, triggering aggressive garbage collection cycles (142 GCs/hour) causing latency spikes.
  * Under `rocksdb_provider` (RocksDB), Heap usage remains stable and low (~12%) as state is maintained off-heap, keeping GC invocation count close to zero.

---

## 3. API Serving Bottleneck Profiling (`gateway_bottleneck_profiles.json`)
* **Objective**: Deconstruct and isolate Uvicorn framework, NumPy inference, and JWT token decryption latency contributions under peak load (1000 QPS).
* **Findings**:
  * **Framework Baseline**: Uvicorn + FastAPI event loop overhead is sub-millisecond (**0.85 ms**).
  * **Pure Inference**: NumPy dot product matrix multiplication is extremely fast (**1.22 ms**).
  * **JWT Validation Overhead**: Cryptographic RSA/HMAC decryption of JWT tokens adds **3.64 ms** of CPU blocking time, causing the single-threaded event loop to stall and driving CPU saturation to **98.5%**.

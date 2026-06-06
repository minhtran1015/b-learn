# Benchmark Notes

## Operational cautions

- The repo targets `aks-blearn-dev` in `RG-BLEarn-Compute`, but the suite accepts env overrides if a different cluster name is used.
- Run `make demo-connect` after the nodes are ready so `http://localhost:8000` and `http://localhost:8080` resolve before the gateway and frontend tests.
- The gateway stress test logs in through `/login` and then calls `/recommendations/{student_hash}` with the JWT bearer token.
- The ingestion benchmark expects Kafka to be reachable at `KAFKA_BOOTSTRAP_SERVERS` and writes events to `learning-events` by default.
- The streaming job now logs rejected payloads with `_corrupt_record` and invalid click types so the poison-pill audit has a concrete signal.
- `kubectl top` requires metrics-server; if it is not available, the greenops step falls back to the last known values in the CSV template.

## Artifact contract

- `throughput_benchmark.json` captures the ingestion throughput and reject counts.
- `latency_stress_test.csv` stores the p50 / p95 / p99 latency rows for the four gateway QPS levels.
- `fault_tolerance_log.json` records the Kafka crash and recovery timestamps.
- `greenops_metrics.csv` stores the baseline vs. suspended resource and cost snapshot.
"""
traffic_generator.py — Simple Kafka traffic generator for live streaming demos.

Sends OULAD-shaped click events every 2 seconds using kafka-python-ng.
"""

import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaProducer


DEFAULT_STUDENTS = [
    "student-001",
    "student-002",
    "student-003",
    "student-004",
    "student-005",
]

DEFAULT_MODULES = ["AAA", "BBB", "CCC", "DDD"]
DEFAULT_PRESENTATIONS = ["2013J", "2014J", "2013B", "2014B"]
DEFAULT_SITES = [
    527388,
    811964,
    6790,
    877915,
    927895,
    1043843,
]


def _load_student_ids() -> list[str]:
    env_value = os.getenv("TRAFFIC_GENERATOR_STUDENTS", "").strip()
    if env_value:
        students = [value.strip() for value in env_value.split(",") if value.strip()]
        if students:
            return students

    serving_root = os.getenv("TRAFFIC_GENERATOR_SERVING_ROOT", "").strip()
    if serving_root:
        try:
            import pandas as pd

            parquet_uri = serving_root.rstrip("/") + "/user_embeddings.parquet"
            storage_options = {
                "account_name": os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026"),
                "account_key": os.getenv("AZURE_STORAGE_KEY"),
            }
            user_embeddings = pd.read_parquet(parquet_uri, storage_options=storage_options)
            ids = [str(value) for value in user_embeddings["student_id_hash"].dropna().astype(str).tolist()]
            if ids:
                return ids
        except Exception as exc:
            print(f"⚠️ Could not load student ids from serving root: {exc}")

    return DEFAULT_STUDENTS


def _build_producer() -> KafkaProducer:
    bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "kafka-service.blearn-medallion.svc.cluster.local:9092"
    )
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        linger_ms=0,
        acks=1,
        retries=0,
        max_block_ms=1000,
    )


def _build_event(student_id_hash: str) -> dict:
    site_id = random.choice(DEFAULT_SITES)
    module = random.choice(DEFAULT_MODULES)
    presentation = random.choice(DEFAULT_PRESENTATIONS)
    return {
        "event_type": "click",
        "student_id_hash": student_id_hash,
        "code_module": module,
        "code_presentation": presentation,
        "id_site": site_id,
        "date": random.randint(0, 250),
        "sum_click": random.randint(1, 8),
        "event_time": datetime.now(timezone.utc).isoformat(),
        "source": "traffic_generator",
    }


def main() -> None:
    topic = os.getenv("KAFKA_TOPIC", "learning-events")
    interval_seconds = float(os.getenv("TRAFFIC_GENERATOR_INTERVAL_SECONDS", "2"))
    students = _load_student_ids()
    producer = _build_producer()

    print(f"🚦 Starting traffic generator on topic '{topic}' with {len(students)} students...")
    while True:
        student_id_hash = random.choice(students)
        event = _build_event(student_id_hash)
        producer.send(topic, event)
        print(f"→ sent click event for {student_id_hash} / site {event['id_site']}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ManifestRecord:
    source_path: str
    dataset: str
    table: str
    file_type: str
    partition_hint: str
    ingest_strategy: str

    def to_json(self) -> str:
        return json.dumps({
            "source_path": self.source_path,
            "dataset": self.dataset,
            "table": self.table,
            "file_type": self.file_type,
            "partition_hint": self.partition_hint,
            "ingest_strategy": self.ingest_strategy,
        }, ensure_ascii=False)


def normalize_table_name(value: str) -> str:
    result = []
    previous_underscore = False
    for char in value.lower():
        if char.isalnum():
            result.append(char)
            previous_underscore = False
        else:
            if not previous_underscore:
                result.append("_")
                previous_underscore = True
    normalized = "".join(result).strip("_")
    return normalized or "table"


def resolve_dataset_record(source_root: Path, file_path: Path) -> ManifestRecord | None:
    relative = file_path.relative_to(source_root)
    parts = relative.parts

    if not parts:
        return None

    top_level = parts[0]
    suffix = file_path.suffix.lower()

    if len(parts) == 1 and file_path.name == "Question_Bank.json":
        return ManifestRecord(
            source_path=str(file_path),
            dataset="content",
            table="content_question_bank",
            file_type="json",
            partition_hint="_ingest_date",
            ingest_strategy="json",
        )

    if len(parts) == 1 and file_path.name == "Lecture_Bank.json":
        return ManifestRecord(
            source_path=str(file_path),
            dataset="content",
            table="content_lecture_bank",
            file_type="json",
            partition_hint="_ingest_date",
            ingest_strategy="json",
        )

    if top_level == "EdNet":
        if len(parts) >= 3 and parts[1] in {"KT1", "KT2", "KT3", "KT4"} and suffix == ".csv":
            table_map = {
                "KT1": "ednet_kt1_events",
                "KT2": "ednet_kt2_events",
                "KT3": "ednet_kt3_events",
                "KT4": "ednet_kt4_events",
            }
            return ManifestRecord(
                source_path=str(file_path),
                dataset="ednet",
                table=table_map[parts[1]],
                file_type="csv",
                partition_hint="_ingest_date",
                ingest_strategy="csv",
            )

        if len(parts) >= 3 and parts[1] == "contents" and suffix == ".csv":
            stem = normalize_table_name(file_path.stem)
            return ManifestRecord(
                source_path=str(file_path),
                dataset="ednet",
                table=f"ednet_{stem}",
                file_type="csv",
                partition_hint="_ingest_date",
                ingest_strategy="csv",
            )

        if suffix == ".json":
            if file_path.name == "Question_Bank.json":
                return ManifestRecord(
                    source_path=str(file_path),
                    dataset="ednet",
                    table="ednet_question_bank",
                    file_type="json",
                    partition_hint="_ingest_date",
                    ingest_strategy="json",
                )
            if file_path.name == "Lecture_Bank.json":
                return ManifestRecord(
                    source_path=str(file_path),
                    dataset="ednet",
                    table="ednet_lecture_bank",
                    file_type="json",
                    partition_hint="_ingest_date",
                    ingest_strategy="json",
                )

    if top_level == "SED" and suffix == ".csv":
        stem = normalize_table_name(file_path.stem)
        return ManifestRecord(
            source_path=str(file_path),
            dataset="sed",
            table=f"sed_{stem}",
            file_type="csv",
            partition_hint="_ingest_date",
            ingest_strategy="csv",
        )

    if top_level == "OULAD" and suffix == ".csv":
        stem = normalize_table_name(file_path.stem)
        partition_hint = "code_module" if stem != "studentvle" else "code_module"
        return ManifestRecord(
            source_path=str(file_path),
            dataset="oulad",
            table=f"oulad_{stem}",
            file_type="csv",
            partition_hint=partition_hint,
            ingest_strategy="csv",
        )

    if top_level == "Data" and suffix == ".md":
        stem = normalize_table_name(file_path.stem)
        return ManifestRecord(
            source_path=str(file_path),
            dataset="content",
            table="content_documents",
            file_type="markdown",
            partition_hint="chapter",
            ingest_strategy=f"markdown:{stem}",
        )

    return None


def discover_files(source_root: Path) -> list[ManifestRecord]:
    records: list[ManifestRecord] = []

    root_question_bank = source_root / "Question_Bank.json"
    root_lecture_bank = source_root / "Lecture_Bank.json"

    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.name in {"Question_Bank.json", "Lecture_Bank.json"} and file_path.parent.name == "EdNet":
            if (file_path.name == root_question_bank.name and root_question_bank.exists()) or (
                file_path.name == root_lecture_bank.name and root_lecture_bank.exists()
            ):
                continue

        record = resolve_dataset_record(source_root, file_path)
        if record is not None:
            records.append(record)

    return records


def write_manifest(records: Iterable[ManifestRecord], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.to_json())
            handle.write("\n")


def load_manifest(manifest_path: Path) -> list[dict[str, str]]:
    records = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records

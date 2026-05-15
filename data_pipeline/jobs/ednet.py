"""EdNet job-specific configs and helpers."""

DEFAULTS = {
    "dataset": "ednet",
    "partition_hint": "_ingest_date",
}


def table_for_path(path_segments: list[str], filename: str) -> str:
    # Minimal helper: derive table name from path segments (KT1/KT2/contents/...)
    if len(path_segments) >= 2 and path_segments[1] in {"KT1", "KT2", "KT3", "KT4"}:
        return f"ednet_{path_segments[1].lower()}_events"
    if filename.endswith("Lecture_Bank.json"):
        return "ednet_lecture_bank"
    if filename.endswith("Question_Bank.json"):
        return "ednet_question_bank"
    return f"ednet_{filename.split('.')[0].lower()}"

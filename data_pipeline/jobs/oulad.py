"""OULAD job-specific configs and helpers."""

DEFAULTS = {
    "dataset": "oulad",
    "partition_hint": "code_module",
}

SOURCE_TABLES = [
    "oulad_courses",
    "oulad_assessments",
    "oulad_studentinfo",
    "oulad_studentregistration",
    "oulad_studentassessment",
    "oulad_studentvle",
    "oulad_vle",
]

CUTOFF_DAY = 30

TARGET_MAP = {
    "Withdrawn": "Withdrawn",
    "Fail": "Fail",
    "Pass": "Success",
    "Distinction": "Success",
}

GOLD_FEATURE_COLUMNS = [
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "num_of_prev_attempts",
    "studied_credits",
    "disability",
    "total_clicks",
    "active_days",
    "avg_daily_clicks",
    "max_clicks_day",
    "engagement_span",
    "recent_weekly_rate",
    "recency_days",
    "engagement_momentum",
    "avg_score",
    "min_score",
    "submission_count",
    "late_submissions",
    "weighted_avg",
]

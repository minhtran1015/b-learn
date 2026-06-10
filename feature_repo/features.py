from datetime import timedelta
from feast import (
    Entity,
    FeatureView,
    Field,
    FileSource,
)
from feast.types import Float32, Int64, String

# Define student entity using their anonymized ID hash
student = Entity(
    name="student_id_hash",
    value_type=Entity.ValueType.STRING,
    description="The SHA-256 anonymized student identifier",
)

# File sources referencing the Iceberg exported parquet files on ADLS Gen2
student_features_source = FileSource(
    path="/tmp/risk_features.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# Define Feast Feature View grouping studied credits, click activities, and risk predictions
student_behavior_fv = FeatureView(
    name="student_behavior_features",
    entities=[student],
    ttl=timedelta(days=365),
    schema=[
        Field(name="num_of_prev_attempts", dtype=Int64),
        Field(name="studied_credits", dtype=Int64),
        Field(name="total_clicks", dtype=Int64),
        Field(name="active_days", dtype=Int64),
        Field(name="avg_daily_clicks", dtype=Float32),
        Field(name="avg_score", dtype=Float32),
        Field(name="submission_count", dtype=Int64),
        Field(name="gender", dtype=String),
        Field(name="region", dtype=String),
        Field(name="highest_education", dtype=String),
        Field(name="dropout_probability", dtype=Float32),
    ],
    online=True,
    source=student_features_source,
    tags={"team": "b-learn-recsys"},
)

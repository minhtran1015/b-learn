from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

import joblib
import numpy as np
import pandas as pd
from azure.storage.blob import BlobServiceClient
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from sklearn.base import clone

from ingestion.ingest import _abfss_container, build_spark, write_table
from jobs.oulad import CUTOFF_DAY, GOLD_FEATURE_COLUMNS, SOURCE_TABLES

DEFAULT_INPUT_CATALOG = "silver_catalog"
DEFAULT_INPUT_NAMESPACE = "silver_db"
DEFAULT_OUTPUT_CATALOG = "gold_catalog"
DEFAULT_OUTPUT_NAMESPACE = "gold"
DEFAULT_OUTPUT_ROOT = (
    f"abfss://gold@{os.getenv('AZURE_STORAGE_ACCOUNT', 'stblearnminhdata2026')}"
    ".dfs.core.windows.net/iceberg_warehouse/gold/"
)
DEFAULT_MODEL_BLOB = "models/oulad_lgbm_pipeline.joblib"
DEFAULT_METRICS_BLOB = "models/oulad_lgbm_metrics.json"

NUMERIC_FEATURES = [
    "num_of_prev_attempts",
    "studied_credits",
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

CATEGORICAL_FEATURES = [
    "code_module",
    "code_presentation",
    "gender",
    "region",
    "highest_education",
    "imd_band",
    "age_band",
    "disability",
]


def _ensure_columns(df: DataFrame, columns: list[str]) -> DataFrame:
    for column_name in columns:
        if column_name not in df.columns:
            df = df.withColumn(column_name, F.lit(None))
    return df


def _build_vle_features(vle: DataFrame) -> DataFrame:
    windowed = vle.where(F.col("date").isNotNull() & (F.col("date") <= F.lit(CUTOFF_DAY)))

    base = windowed.groupBy("id_student", "code_module", "code_presentation").agg(
        F.sum("sum_click").alias("total_clicks"),
        F.countDistinct("date").alias("active_days"),
        F.avg("sum_click").alias("avg_daily_clicks"),
        F.max("sum_click").alias("max_clicks_day"),
        F.min("date").alias("first_activity"),
        F.max("date").alias("last_activity"),
    )
    base = base.withColumn("engagement_span", F.col("last_activity") - F.col("first_activity"))

    recent = (
        windowed.where((F.col("date") > F.lit(CUTOFF_DAY - 7)) & (F.col("date") <= F.lit(CUTOFF_DAY)))
        .groupBy("id_student", "code_module", "code_presentation")
        .agg(F.sum("sum_click").alias("recent_clicks_sum"))
        .withColumn("recent_weekly_rate", F.col("recent_clicks_sum") / F.lit(7.0))
        .drop("recent_clicks_sum")
    )

    return (
        base.join(recent, on=["id_student", "code_module", "code_presentation"], how="left")
        .withColumn("recency_days", F.lit(CUTOFF_DAY) - F.coalesce(F.col("last_activity"), F.lit(0)))
        .withColumn(
            "engagement_momentum",
            F.coalesce(F.col("recent_weekly_rate"), F.lit(0.0)) - F.coalesce(F.col("avg_daily_clicks"), F.lit(0.0)),
        )
    )


def _build_assessment_features(studentassessment: DataFrame, assessments: DataFrame) -> DataFrame:
    assess_joined = (
        studentassessment.alias("sa")
        .join(
            assessments.select("id_assessment", "code_module", "code_presentation", "weight", "date").alias("a"),
            on="id_assessment",
            how="left",
        )
        .where(F.col("date").isNull() | (F.col("date") <= F.lit(CUTOFF_DAY)))
    )

    agg = assess_joined.groupBy(
        F.col("id_student"),
        F.col("sa.code_module"),
        F.col("sa.code_presentation"),
    ).agg(
        F.avg("score").alias("avg_score"),
        F.min("score").alias("min_score"),
        F.count("id_assessment").alias("submission_count"),
        F.sum(F.coalesce(F.col("is_banked"), F.lit(0))).alias("late_submissions"),
        F.sum(F.col("score") * F.coalesce(F.col("weight"), F.lit(0.0))).alias("weighted_score_sum"),
        F.sum(F.coalesce(F.col("weight"), F.lit(0.0))).alias("weight_sum"),
    )

    return agg.withColumn(
        "weighted_avg",
        F.when(F.col("weight_sum") > 0, F.col("weighted_score_sum") / F.col("weight_sum")).otherwise(F.lit(None)),
    ).drop("weighted_score_sum", "weight_sum")


def _build_gold_features(
    studentinfo: DataFrame,
    studentregistration: DataFrame,
    studentassessment: DataFrame,
    studentvle: DataFrame,
    assessments: DataFrame,
) -> DataFrame:
    keys = ["id_student", "code_module", "code_presentation"]

    base = (
        studentinfo.select(
            "id_student",
            "code_module",
            "code_presentation",
            "gender",
            "region",
            "highest_education",
            "imd_band",
            "age_band",
            F.col("num_of_prev_attempts").cast("int").alias("num_of_prev_attempts"),
            F.col("studied_credits").cast("int").alias("studied_credits"),
            "disability",
            "final_result",
        )
    )

    registration = studentregistration.select(
        "id_student",
        "code_module",
        "code_presentation",
        F.col("date_registration").cast("int").alias("date_registration"),
        F.col("date_unregistration").cast("int").alias("date_unregistration"),
    )

    vle_features = _build_vle_features(studentvle)
    assess_features = _build_assessment_features(studentassessment, assessments)

    gold = (
        base.join(registration, on=keys, how="left")
        .join(vle_features, on=keys, how="left")
        .join(assess_features, on=keys, how="left")
        .withColumn(
            "target_class",
            F.when(F.col("final_result") == F.lit("Withdrawn"), F.lit("Withdrawn"))
            .when(F.col("final_result") == F.lit("Fail"), F.lit("Fail"))
            .when(F.col("final_result").isin("Pass", "Distinction"), F.lit("Success"))
            .otherwise(F.lit(None)),
        )
        .withColumn("is_at_risk", F.when(F.col("target_class").isin("Withdrawn", "Fail"), F.lit(1)).otherwise(F.lit(0)))
    )

    for column_name in GOLD_FEATURE_COLUMNS:
        if column_name not in gold.columns:
            gold = gold.withColumn(column_name, F.lit(None))

    fill_values = {
        "num_of_prev_attempts": 0,
        "studied_credits": 0,
        "total_clicks": 0,
        "active_days": 0,
        "avg_daily_clicks": 0.0,
        "max_clicks_day": 0,
        "engagement_span": 0,
        "recent_weekly_rate": 0.0,
        "recency_days": 0,
        "engagement_momentum": 0.0,
        "avg_score": 0.0,
        "min_score": 0.0,
        "submission_count": 0,
        "late_submissions": 0,
        "weighted_avg": 0.0,
    }
    gold = gold.fillna(fill_values)
    gold = gold.fillna({c: "Unknown" for c in CATEGORICAL_FEATURES})
    return gold


def _train_lgbm(features: pd.DataFrame) -> tuple[Pipeline, dict[str, float], LabelEncoder, pd.DataFrame, np.ndarray, np.ndarray]:
    working = features.copy()
    working["target_class"] = working["target_class"].replace({None: "Unknown"})
    working = working[working["target_class"].isin(["Withdrawn", "Fail", "Success"])]
    working = working.dropna(subset=["target_class"])

    test_presentations = [p for p in working["code_presentation"].astype(str).unique() if "2014" in p]
    if test_presentations:
        train_df = working[~working["code_presentation"].astype(str).isin(test_presentations)].copy()
        test_df = working[working["code_presentation"].astype(str).isin(test_presentations)].copy()
        if test_df.empty or train_df.empty:
            train_df, test_df = train_test_split(
                working,
                test_size=0.2,
                random_state=42,
                stratify=working["target_class"],
            )
    else:
        train_df, test_df = train_test_split(
            working,
            test_size=0.2,
            random_state=42,
            stratify=working["target_class"],
        )

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_df["target_class"])
    y_test = label_encoder.transform(test_df["target_class"])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), NUMERIC_FEATURES),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    X_train = train_df[GOLD_FEATURE_COLUMNS]
    X_test = test_df[GOLD_FEATURE_COLUMNS]

    X_fit_raw, X_valid_raw, y_fit, y_valid = train_test_split(
        X_train,
        y_train,
        test_size=0.2,
        random_state=42,
        stratify=y_train,
    )

    preprocessor_es = clone(preprocessor)
    X_fit_proc = preprocessor_es.fit_transform(X_fit_raw)
    X_valid_proc = preprocessor_es.transform(X_valid_raw)

    lgbm_es = LGBMClassifier(
        learning_rate=0.05,
        objective="multiclass",
        random_state=42,
        n_estimators=5000,
        device_type="cpu",
        verbosity=-1,
        n_jobs=-1,
    )
    lgbm_es.fit(
        X_fit_proc,
        y_fit,
        eval_set=[(X_valid_proc, y_valid)],
        eval_metric="multi_logloss",
        callbacks=[early_stopping(stopping_rounds=100, verbose=False), log_evaluation(period=0)],
    )

    best_n_estimators = int(getattr(lgbm_es, "best_iteration_", 0) or lgbm_es.n_estimators)
    final_pipeline = Pipeline(
        steps=[
            ("preprocessor", clone(preprocessor)),
            (
                "model",
                LGBMClassifier(
                    learning_rate=0.05,
                    objective="multiclass",
                    random_state=42,
                    n_estimators=int(best_n_estimators * 1.25),
                    device_type="cpu",
                    verbosity=-1,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    final_pipeline.fit(X_train, y_train)

    proba = final_pipeline.predict_proba(X_test)
    preds = np.argmax(proba, axis=1)
    metrics = {
        "test_pr_auc": float(np.nanmean([
            average_precision_score((y_test == class_idx).astype(int), proba[:, class_idx])
            for class_idx in range(proba.shape[1])
        ])),
        "best_n_estimators": float(best_n_estimators),
    }
    print(classification_report(y_test, preds, target_names=label_encoder.classes_))
    print(f"LightGBM PR-AUC={metrics['test_pr_auc']:.4f}")
    return final_pipeline, metrics, label_encoder, test_df, y_test, preds


def _upload_blob(storage_account: str, storage_key: str, container: str, blob_name: str, payload_path: Path) -> None:
    service = BlobServiceClient(
        account_url=f"https://{storage_account}.blob.core.windows.net",
        credential=storage_key,
    )
    blob_client = service.get_blob_client(container=container, blob=blob_name)
    with payload_path.open("rb") as handle:
        blob_client.upload_blob(handle, overwrite=True)


def run_gold_pipeline(
    spark,
    input_catalog: str,
    input_namespace: str,
    output_root: str,
    output_catalog: str,
    output_namespace: str,
    model_blob: str,
    metrics_blob: str,
) -> None:
    required_tables = {table_name: spark.table(f"{input_catalog}.{input_namespace}.{table_name}") for table_name in SOURCE_TABLES}

    gold = _build_gold_features(
        required_tables["oulad_studentinfo"],
        required_tables["oulad_studentregistration"],
        required_tables["oulad_studentassessment"],
        required_tables["oulad_studentvle"],
        required_tables["oulad_assessments"],
    )

    write_table(
        gold,
        output_root,
        "oulad_at_risk_features",
        partition_hint="code_module",
        namespace=output_namespace,
        catalog_name=output_catalog,
    )

    pandas_gold = gold.select(*(GOLD_FEATURE_COLUMNS + ["target_class", "code_module", "code_presentation", "id_student"])).toPandas()
    pipeline, metrics, label_encoder, test_df, y_test, preds = _train_lgbm(pandas_gold)

    scored = pipeline.predict_proba(pandas_gold[GOLD_FEATURE_COLUMNS])
    scored_df = pd.DataFrame(scored, columns=[f"prob_{label}" for label in label_encoder.classes_])
    scored_df["predicted_class"] = label_encoder.inverse_transform(np.argmax(scored, axis=1))
    scored_df["at_risk_probability"] = scored_df.get("prob_Withdrawn", 0) + scored_df.get("prob_Fail", 0)
    scored_df["id_student"] = pandas_gold["id_student"].values
    scored_df["code_module"] = pandas_gold["code_module"].values
    scored_df["code_presentation"] = pandas_gold["code_presentation"].values

    scored_spark = spark.createDataFrame(scored_df)
    write_table(
        scored_spark,
        output_root,
        "oulad_at_risk_predictions",
        partition_hint="code_module",
        namespace=output_namespace,
        catalog_name=output_catalog,
    )

    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT", "stblearnminhdata2026")
    storage_key = os.getenv("AZURE_STORAGE_KEY")
    blob_container = _abfss_container(output_root) or "gold"
    if storage_key:
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "oulad_lgbm_pipeline.joblib"
            metrics_path = Path(temp_dir) / "oulad_lgbm_metrics.json"
            joblib.dump(pipeline, model_path)
            metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
            _upload_blob(storage_account, storage_key, blob_container, model_blob, model_path)
            _upload_blob(storage_account, storage_key, blob_container, metrics_blob, metrics_path)
            print(f"Uploaded model artifact to {model_blob}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize OULAD Gold features and train LightGBM on ADLS")
    parser.add_argument("--input-catalog", default=DEFAULT_INPUT_CATALOG)
    parser.add_argument("--input-namespace", default=DEFAULT_INPUT_NAMESPACE)
    parser.add_argument("--output-catalog", default=DEFAULT_OUTPUT_CATALOG)
    parser.add_argument("--output-namespace", default=DEFAULT_OUTPUT_NAMESPACE)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--input-container", default="silver")
    parser.add_argument("--output-container", default="gold")
    parser.add_argument("--model-blob", default=DEFAULT_MODEL_BLOB)
    parser.add_argument("--metrics-blob", default=DEFAULT_METRICS_BLOB)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not str(args.output_root).startswith("abfss://"):
        raise ValueError("Gold job is intended for ADLS deployment; pass an abfss:// output root.")

    spark = build_spark(
        "B-Learn_Gold_OULAD_LGBM",
        args.output_root,
        iceberg_catalogs={args.input_catalog: args.input_container, args.output_catalog: args.output_container},
        default_catalog_name=args.output_catalog,
    )
    try:
        run_gold_pipeline(
            spark,
            args.input_catalog,
            args.input_namespace,
            args.output_root,
            args.output_catalog,
            args.output_namespace,
            args.model_blob,
            args.metrics_blob,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

# data_pipeline/dags/oulad_medallion_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

default_args = {
    'owner': 'trandinhquangminh',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'oulad_medallion_pipeline',
    default_args=default_args,
    schedule_interval=None, # Chỉ chạy khi bấm nút Demo
    catchup=False,
    tags=['b-learn', 'oulad'],
) as dag:

    # Cấu hình biến môi trường nạp Key/Account từ K8s Secret 'oulad-runtime' vào Pod của Airflow
    env_vars = [
        k8s.V1EnvVar(
            name="AZURE_STORAGE_ACCOUNT",
            value_from=k8s.V1EnvVarSource(
                secret_key_ref=k8s.V1SecretKeySelector(
                    name="oulad-runtime",
                    key="AZURE_STORAGE_ACCOUNT"
                )
            )
        ),
        k8s.V1EnvVar(
            name="AZURE_STORAGE_KEY",
            value_from=k8s.V1EnvVarSource(
                secret_key_ref=k8s.V1SecretKeySelector(
                    name="oulad-runtime",
                    key="AZURE_STORAGE_KEY"
                )
            )
        ),
        k8s.V1EnvVar(name="SPARK_DRIVER_MEMORY", value="4g")
    ]

    image_path = "acrblearnminh2026.azurecr.io/oulad-medallion:latest"

    # Task 1: Ingest dữ liệu thô vào lớp Bronze
    bronze_ingest = KubernetesPodOperator(
        task_id='bronze_ingest',
        name='airflow-bronze-ingest',
        image=image_path,
        cmds=["python", "-m", "data_pipeline.ingestion.ingest"],
        arguments=[
            "--manifest-path", "full_data_manifest.json",
            "--output-root", "abfss://bronze@stblearnminhdata2026.dfs.core.windows.net/iceberg_warehouse/full/",
            "ingest", "--namespace", "full"
        ],
        env_vars=env_vars,
        get_logs=True
    )

    # Task 2: Chuẩn hóa dữ liệu sang lớp Silver (Băm SHA256, ép kiểu)
    silver_transform = KubernetesPodOperator(
        task_id='silver_transform',
        name='airflow-silver-transform',
        image=image_path,
        cmds=["python", "-m", "data_pipeline.silver.oulad"],
        env_vars=env_vars,
        get_logs=True
    )

    # Task 3: Tính toán Feature & Huấn luyện mô hình tại tầng Gold
    gold_feature_model = KubernetesPodOperator(
        task_id='gold_feature_model',
        name='airflow-gold-model',
        image=image_path,
        cmds=["python", "-m", "data_pipeline.gold.oulad"],
        env_vars=env_vars,
        get_logs=True
    )

    # Định nghĩa luồng chạy tuần tự
    bronze_ingest >> silver_transform >> gold_feature_model

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s
from datetime import datetime, timedelta

# Define hostPath volume and mount properly
host_volume = k8s.V1Volume(
    name="host-volume",
    host_path=k8s.V1HostPathVolumeSource(
        path="host/projects/recsys1/data",
        type="Directory"
    )
)

host_volume_mount = k8s.V1VolumeMount(
    name="host-volume",
    mount_path="/hostdata",
    read_only=False
)

with DAG(
    "reddit_pipeline",
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=["reddit", "clip", "qdrant"],
) as dag:

    ingest_task = KubernetesPodOperator(
        task_id="ingest_reddit_images",
        namespace="airflow",
        name="ingest-reddit-images",
        image="python:3.11-slim",
        cmds=["python", "-u", "/hostdata/scripts/reddit_ingest.py"],
        startup_timeout_seconds=300,
        volumes=[host_volume],
        volume_mounts=[host_volume_mount],
        is_delete_operator_pod=True,
        get_logs=True,
    )

    featurize_task = KubernetesPodOperator(
        task_id="featurize_clip_embeddings",
        namespace="airflow",
        name="featurize-clip-embeddings",
        image="python:3.11-slim",
        cmds=["python", "-u", "/hostdata/scripts/featurize.py"],
        volumes=[host_volume],
        startup_timeout_seconds=300,
        volume_mounts=[host_volume_mount],
        is_delete_operator_pod=True,
        get_logs=True,
    )

    ingest_task >> featurize_task
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime, timedelta
import subprocess
import os


def run_script(script_name):
    """Generic wrapper to call a Python script inside scripts/"""
    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", script_name)
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Error running {script_name}: {result.stderr}")
    print(result.stdout)


with DAG(
    "reddit_pipeline",
    default_args={
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    },
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(hours=1), # Runs every hour
    catchup=False,
    tags=["reddit", "clip", "qdrant"],
) as dag:

    ingest_task = KubernetesPodOperator(
        task_id="ingest_reddit_images",
        namespace="default",
        name="ingest-reddit-images",
        image="python:3.11-slim",
        cmds=["python", "-u", "/hostdata/scripts/reddit_ingest.py"],
        volumes=[{
            "name": "host-volume",
            "hostPath": {"path": "/data", "type": "Directory"}
        }],
        volume_mounts=[{
            "name": "host-volume",
            "mountPath": "/hostdata",
            "readOnly": False
        }],
        is_delete_operator_pod=True,
        get_logs=True,
    )

    featurize_task = KubernetesPodOperator(
        task_id="featurize_clip_embeddings",
        namespace="default",
        name="featurize-clip-embeddings",
        image="python:3.11-slim",
        cmds=["python", "-u", "/hostdata/scripts/featurize.py"],
        volumes=[{
            "name": "host-volume",
            "hostPath": {"path": "/data", "type": "Directory"}
        }],
        volume_mounts=[{
            "name": "host-volume",
            "mountPath": "/hostdata",
            "readOnly": False
        }],
        is_delete_operator_pod=True,
        get_logs=True,
    )

    ingest_task >> featurize_task
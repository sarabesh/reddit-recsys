from airflow.sdk import DAG
from airflow.operators.python import PythonOperator
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

    ingest_task = PythonOperator(
        task_id="ingest_reddit_images",
        python_callable=lambda: run_script("reddit_ingest.py"),
    )

    featurize_task = PythonOperator(
        task_id="featurize_clip_embeddings",
        python_callable=lambda: run_script("featurize.py"),
    )

    upload_task = PythonOperator(
        task_id="upload_to_qdrant",
        python_callable=lambda: run_script("upload_qdrant.py"),
    )

    ingest_task >> featurize_task >> upload_task

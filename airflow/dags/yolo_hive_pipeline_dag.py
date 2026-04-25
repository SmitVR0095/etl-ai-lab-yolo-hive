"""DAG opcional para orquestar clasificación YOLO y ETL hacia Hive."""
from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/home/smit_vr/cursobsgetl/codigo/etl-ai-lab"
VENV_ACTIVATE = "/home/smit_vr/cursobsgetl/ambientes/etl-ai-lab/bin/activate"

with DAG(
    dag_id="yolo_hive_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["yolo", "hive", "vision"],
) as dag:
    classify = BashOperator(
        task_id="clasificar_imagenes_y_videos",
        bash_command=f"cd {PROJECT_DIR} && source {VENV_ACTIVATE} && python src/sistema_clasificacion.py --mode all",
    )

    etl = BashOperator(
        task_id="etl_csv_hacia_hive",
        bash_command=f"cd {PROJECT_DIR} && source {VENV_ACTIVATE} && python src/sistema_batch_etl.py --beeline-url jdbc:hive2://localhost:10000/yolo_project && beeline -u jdbc:hive2://localhost:10000/yolo_project -f sql/02_merge_without_duplicates.sql",
    )

    classify >> etl

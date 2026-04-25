from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import os

def extract():
    print("Extrayendo datos desde API...")
    with open("/mnt/data/etl-ai-lab/airflow/data/raw_data.txt", "w") as f:
        f.write("ventas,region,revenue\n100,Sur,2500\n200,Norte,3800\n")

def load():
    print("Cargando datos transformados al Data Warehouse...")

default_args = {
    'owner': 'smit_vr',
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'start_date': datetime(2025, 10, 14),
}

with DAG(
    dag_id='etl_pipeline_demo',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Pipeline ETL con Airflow y Spark'
) as dag:

    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=extract
    )

    spark_task = SparkSubmitOperator(
        task_id='spark_transform',
        application='/mnt/data/etl-ai-lab/spark_jobs/transform_job.py',
        conn_id='spark_default',
        application_args=[
            '--input', '/home/smit_vr/cursobsgetl/codigo/etl-ai-lab/airflow/data/raw_data.txt', # /mnt/data/etl-ai-lab/airflow/data/raw_data.txt
            '--output', '/home/smit_vr/cursobsgetl/codigo/etl-ai-lab/airflow/data/processed_data.parquet' # /mnt/data/etl-ai-lab/airflow/data/processed_data.parquet
        ],
        verbose=True
    )

    load_task = PythonOperator(
        task_id='load_data',
        python_callable=load
    )

    extract_task >> spark_task >> load_task

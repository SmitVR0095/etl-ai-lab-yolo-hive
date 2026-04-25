#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

export SPARK_LOCAL_IP=127.0.0.1

BASE_DIR="$(pwd)"

INPUT="file://${BASE_DIR}/airflow/data/sales_data.csv"
OUTPUT="file://${BASE_DIR}/airflow/data/out_parquet"

spark-submit \
    --properties-file configs/spark-defaults.conf \
    spark_jobs/transform_job.py \
    --input "$INPUT" \
    --output "$OUTPUT"
#!/usr/bin/env bash
source /home/smit_vr/cursobsgetl/ambientes/etl-ai-lab/bin/activate
export AIRFLOW_HOME=/home/smit_vr/cursobsgetl/codigo/etl-ai-lab/airflow

echo "PYTHON      : $(which python)"
echo "AIRFLOW     : $(which airflow)"
echo "AIRFLOW_HOME: $AIRFLOW_HOME"
echo "DB          : $(airflow config get-value database sql_alchemy_conn)"

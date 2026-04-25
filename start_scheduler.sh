#!/usr/bin/env bash
source /home/smit_vr/cursobsgetl/codigo/etl-ai-lab/airflow_env.sh
mkdir -p $AIRFLOW_HOME/runtime
airflow db check || exit 1
exec airflow scheduler
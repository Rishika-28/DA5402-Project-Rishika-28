from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="rossmann_sales_forecasting_pipeline",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    schedule=None,
    tags=["mlops", "forecasting", "rossmann"],
) as dag:
    prepare_data = BashOperator(
        task_id="prepare_data",
        bash_command="python -m src.data_pipeline prepare --params params.yaml",
    )

    train_model = BashOperator(
        task_id="train_model",
        bash_command="python -m src.train --params params.yaml",
    )

    evaluate_model = BashOperator(
        task_id="evaluate_model",
        bash_command="python -m src.evaluate --params params.yaml",
    )

    prepare_data >> train_model >> evaluate_model


from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


with DAG(
    dag_id="pipeline__seoul__raw_only",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["seoul", "pipeline", "raw"],
) as dag:

    start = EmptyOperator(task_id="start")

    extract_all = TriggerDagRunOperator(
        task_id="extract__all",
        trigger_dag_id="seoul_extract_all_raw_zips",  # zipz 오타 제거
        wait_for_completion=True,
        poke_interval=30,
    )

    lp_2023 = TriggerDagRunOperator(
        task_id="ingest__livingpop__2023",
        trigger_dag_id="ingest__livingpop__year",
        conf={"year": "2023"},
        wait_for_completion=True,
        poke_interval=30,
    )
    lp_2024 = TriggerDagRunOperator(
        task_id="ingest__livingpop__2024",
        trigger_dag_id="ingest__livingpop__year",
        conf={"year": "2024"},
        wait_for_completion=True,
        poke_interval=30,
    )
    lp_2025 = TriggerDagRunOperator(
        task_id="ingest__livingpop__2025",
        trigger_dag_id="ingest__livingpop__year",
        conf={"year": "2025"},
        wait_for_completion=True,
        poke_interval=30,
    )

    sales = TriggerDagRunOperator(
        task_id="ingest__seoul_sales",
        trigger_dag_id="ingest__seoul_sales",
        wait_for_completion=True,
        poke_interval=30,
    )

    vacancy = TriggerDagRunOperator(
        task_id="ingest__vacancy",
        trigger_dag_id="ingest__vacancy",
        wait_for_completion=True,
        poke_interval=30,
    )

    dim_admin = TriggerDagRunOperator(
        task_id="load__dim_admin_dong",
        trigger_dag_id="load__dim_admin_dong",
        wait_for_completion=True,
        poke_interval=30,
    )

    end = EmptyOperator(task_id="end")

    start >> extract_all >> lp_2023 >> lp_2024 >> lp_2025 >> sales >> vacancy >> dim_admin >> end

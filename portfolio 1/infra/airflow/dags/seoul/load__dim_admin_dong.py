from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

from seoul.config.seoul_config import (
    GCP_CONN_ID,
    BQ_PROJECT,
    BQ_LOCATION,
    BQ_DATASET_RAW,
    BQ_DATASET_MART,
    DEFAULT_ARGS,
    ADMIN_DONG_SOURCE_URI,
    ADMIN_DONG_RAW_TABLE,
    ADMIN_DONG_DIM_TABLE,
)


with DAG(
    dag_id="load__dim_admin_dong",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["seoul", "admin_dong", "dim", "bigquery"],
    max_active_runs=1,
) as dag:

    load_raw = BigQueryInsertJobOperator(
        task_id="load_raw_admin_dong",
        location=BQ_LOCATION,
        configuration={
            "load": {
                "destinationTable": {
                    "projectId": BQ_PROJECT,
                    "datasetId": BQ_DATASET_RAW,
                    "tableId": ADMIN_DONG_RAW_TABLE,
                },
                "sourceUris": [ADMIN_DONG_SOURCE_URI],
                "sourceFormat": "CSV",
                "fieldDelimiter": "\t",
                "encoding": "UTF-8",
                "autodetect": True,
                "writeDisposition": "WRITE_TRUNCATE",
            }
        },
        gcp_conn_id=GCP_CONN_ID,
    )

    build_dim = BigQueryInsertJobOperator(
        task_id="build_dim_admin_dong",
        location=BQ_LOCATION,
        configuration={
            "query": {
                "query": f"""
CREATE OR REPLACE TABLE `{BQ_PROJECT}.{BQ_DATASET_MART}.{ADMIN_DONG_DIM_TABLE}` AS
SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET_RAW}.{ADMIN_DONG_RAW_TABLE}`;
""",
                "useLegacySql": False,
            }
        },
        gcp_conn_id=GCP_CONN_ID,
    )

    load_raw >> build_dim

from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

from seoul.config.seoul_config import (
    GCP_CONN_ID,
    BUCKET,
    BQ_PROJECT,
    BQ_DATASET_RAW,
    BQ_LOCATION,
    DEFAULT_ARGS,
    MIN_BYTES,
    SALES_EXTRACTED_PREFIX,
    SALES_RAW_TABLE,
)

from seoul.utils.seoul_dag_utils import (
    list_gcs_objects_with_size,
    validate_min_size,
    bq_postcheck_rowcount,
)


with DAG(
    dag_id="ingest__seoul_sales",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["seoul", "sales", "bigquery", "raw"],
    max_active_runs=1,
) as dag:

    @task
    def validate_files() -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files = list_gcs_objects_with_size(gcs_hook, BUCKET, SALES_EXTRACTED_PREFIX, suffix=".csv")
        validate_min_size(files, MIN_BYTES, label="sales")
        return {"source_uri": f"gs://{BUCKET}/{SALES_EXTRACTED_PREFIX}*.csv"}

    load_to_bq = BigQueryInsertJobOperator(
        task_id="load_bq_raw",
        location=BQ_LOCATION,
        configuration={
            "load": {
                "destinationTable": {
                    "projectId": BQ_PROJECT,
                    "datasetId": BQ_DATASET_RAW,
                    "tableId": SALES_RAW_TABLE,
                },
                "sourceUris": ["{{ ti.xcom_pull(task_ids='validate_files')['source_uri'] }}"],
                "sourceFormat": "CSV",
                "skipLeadingRows": 1,
                "encoding": "UTF-8",
                "autodetect": True,
                "createDisposition": "CREATE_IF_NEEDED",
                "writeDisposition": "WRITE_TRUNCATE",
                "maxBadRecords": 50,
            }
        },
        gcp_conn_id=GCP_CONN_ID,
    )

    @task
    def postcheck():
        bq_postcheck_rowcount(
            gcp_conn_id=GCP_CONN_ID,
            location=BQ_LOCATION,
            project=BQ_PROJECT,
            dataset=BQ_DATASET_RAW,
            table=SALES_RAW_TABLE,
            label="seoul_sales",
        )

    m = validate_files()
    m >> load_to_bq >> postcheck()

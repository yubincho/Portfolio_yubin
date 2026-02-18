from __future__ import annotations

from datetime import datetime
from typing import List
import os
import tempfile

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
    VACANCY_EXTRACTED_PREFIX,
    VACANCY_NORMALIZED_PREFIX,
    VACANCY_RAW_TABLE,
)

from seoul.utils.seoul_dag_utils import (
    list_gcs_objects_with_size,
    validate_min_size,
    convert_xlsx_to_utf8_csv,
    gcs_upload_file,
    bq_postcheck_rowcount,
)


with DAG(
    dag_id="ingest__vacancy",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["seoul", "vacancy", "xlsx", "normalize", "bigquery", "raw"],
    max_active_runs=1,
) as dag:

    @task
    def list_xlsx_objects() -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files = list_gcs_objects_with_size(gcs_hook, BUCKET, VACANCY_EXTRACTED_PREFIX, suffix=".xlsx")
        validate_min_size(files, MIN_BYTES, label="vacancy")

        xlsx_sorted = sorted([n for (n, _) in files])
        print(f"[vacancy] xlsx files={len(xlsx_sorted)}")
        return {"xlsx_objects": xlsx_sorted}

    @task
    def normalize_xlsx_to_csv(meta: dict) -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        xlsx_objects: List[str] = meta["xlsx_objects"]

        normalized_objects: List[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            for i, obj in enumerate(xlsx_objects, start=1):
                base = os.path.basename(obj)
                local_xlsx = os.path.join(tmp, base)
                local_csv = os.path.join(tmp, base.replace(".xlsx", ".csv"))

                print(f"[vacancy] ({i}/{len(xlsx_objects)}) download: {obj}")
                gcs_hook.download(BUCKET, obj, local_xlsx)

                convert_xlsx_to_utf8_csv(
                    input_path=local_xlsx,
                    output_path=local_csv,
                    label=f"vacancy:{base}",
                )

                out_obj = f"{VACANCY_NORMALIZED_PREFIX}{os.path.basename(local_csv)}"
                print(f"[vacancy] ({i}/{len(xlsx_objects)}) upload: gs://{BUCKET}/{out_obj}")
                gcs_upload_file(gcs_hook, BUCKET, out_obj, local_csv)
                normalized_objects.append(out_obj)

        meta["normalized_objects"] = normalized_objects
        meta["source_uri"] = f"gs://{BUCKET}/{VACANCY_NORMALIZED_PREFIX}*.csv"
        return meta

    load_to_bq = BigQueryInsertJobOperator(
        task_id="load_bq_raw",
        location=BQ_LOCATION,
        configuration={
            "load": {
                "destinationTable": {
                    "projectId": BQ_PROJECT,
                    "datasetId": BQ_DATASET_RAW,
                    "tableId": VACANCY_RAW_TABLE,
                },
                "sourceUris": ["{{ ti.xcom_pull(task_ids='normalize_xlsx_to_csv')['source_uri'] }}"],
                "sourceFormat": "CSV",
                "skipLeadingRows": 1,
                "encoding": "UTF-8",
                "fieldDelimiter": ",",
                "quote": "\"",
                "allowQuotedNewlines": True,
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
            table=VACANCY_RAW_TABLE,
            label="vacancy",
        )

    meta = list_xlsx_objects()
    meta2 = normalize_xlsx_to_csv(meta)
    meta2 >> load_to_bq >> postcheck()

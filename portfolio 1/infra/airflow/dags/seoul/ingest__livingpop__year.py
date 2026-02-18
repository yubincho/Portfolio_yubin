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
    LIVINGPOP_EXTRACTED_BASE,
    LIVINGPOP_NORMALIZED_BASE,
    livingpop_table_id,
)

from seoul.utils.seoul_dag_utils import (
    list_gcs_objects_with_size,
    validate_min_size,
    convert_cp949_csv_to_utf8_stream,
    gcs_upload_file,
    bq_postcheck_rowcount,
)


with DAG(
    dag_id="ingest__livingpop__year",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["seoul", "livingpop", "normalize", "bigquery", "raw"],
    max_active_runs=1,
) as dag:

    @task
    def resolve_year(**context) -> dict:
        conf = (context.get("dag_run") and context["dag_run"].conf) or {}
        year = str(conf.get("year", "2023"))
        if year not in {"2023", "2024", "2025"}:
            raise ValueError(f"year must be one of 2023/2024/2025, got={year}")

        return {
            "year": year,
            "extracted_prefix": f"{LIVINGPOP_EXTRACTED_BASE}{year}/",
            "normalized_prefix": f"{LIVINGPOP_NORMALIZED_BASE}{year}/",
            "table_id": livingpop_table_id(year),
        }

    @task
    def list_and_validate(meta: dict) -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files = list_gcs_objects_with_size(gcs_hook, BUCKET, meta["extracted_prefix"], suffix=".csv")
        print(f"[livingpop] gs://{BUCKET}/{meta['extracted_prefix']} files={len(files)}")
        validate_min_size(files, MIN_BYTES, label="livingpop")
        meta["files"] = sorted([n for (n, _) in files])
        return meta

    @task
    def normalize_to_utf8(meta: dict) -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files: List[str] = meta["files"]
        normalized_prefix = meta["normalized_prefix"]
        year = meta["year"]

        normalized_objects: List[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            for i, obj in enumerate(files, start=1):
                base = os.path.basename(obj)
                local_in = os.path.join(tmp, base)
                local_out = os.path.join(tmp, f"utf8_{base}")

                print(f"[livingpop] ({i}/{len(files)}) download: {obj}")
                gcs_hook.download(BUCKET, obj, local_in)

                rows = convert_cp949_csv_to_utf8_stream(local_in, local_out, f"livingpop:{year}:{base}")
                print(f"[livingpop] ({i}/{len(files)}) converted: {base} rows={rows}")

                out_obj = f"{normalized_prefix}{base}"
                print(f"[livingpop] ({i}/{len(files)}) upload: gs://{BUCKET}/{out_obj}")
                gcs_upload_file(gcs_hook, BUCKET, out_obj, local_out)
                normalized_objects.append(out_obj)

        meta["normalized_objects"] = normalized_objects
        meta["source_uri"] = f"gs://{BUCKET}/{normalized_prefix}*.csv"
        return meta

    load_to_bq = BigQueryInsertJobOperator(
        task_id="load_bq_raw",
        location=BQ_LOCATION,
        configuration={
            "load": {
                "destinationTable": {
                    "projectId": BQ_PROJECT,
                    "datasetId": BQ_DATASET_RAW,
                    "tableId": "{{ ti.xcom_pull(task_ids='resolve_year')['table_id'] }}",
                },
                "sourceUris": ["{{ ti.xcom_pull(task_ids='normalize_to_utf8')['source_uri'] }}"],
                "sourceFormat": "CSV",
                "skipLeadingRows": 1,
                "fieldDelimiter": ",",
                "quote": "\"",
                "allowQuotedNewlines": True,
                "encoding": "UTF-8",
                "autodetect": True,
                "createDisposition": "CREATE_IF_NEEDED",
                "writeDisposition": "WRITE_TRUNCATE",
                "maxBadRecords": 100,
            }
        },
        gcp_conn_id=GCP_CONN_ID,
    )

    @task
    def postcheck(meta: dict):
        bq_postcheck_rowcount(
            gcp_conn_id=GCP_CONN_ID,
            location=BQ_LOCATION,
            project=BQ_PROJECT,
            dataset=BQ_DATASET_RAW,
            table=meta["table_id"],
            label="livingpop",
        )

    meta = resolve_year()
    meta2 = list_and_validate(meta)
    meta3 = normalize_to_utf8(meta2)
    meta3 >> load_to_bq >> postcheck(meta3)

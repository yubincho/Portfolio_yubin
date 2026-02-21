from __future__ import annotations
from datetime import datetime
import os
import tempfile
from typing import List

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
    convert_cp949_csv_to_utf8_stream,
    gcs_upload_file,
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
        
        files_sorted = sorted([n for (n, _) in files])
        return {
            "files": files_sorted,
            "extracted_prefix": SALES_EXTRACTED_PREFIX,
        }

    @task
    def normalize_to_utf8(meta: dict) -> dict:
        """cp949 -> UTF-8 변환 (seoul_dag_utils 함수 사용)"""
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files: List[str] = meta["files"]
        
        # normalized 경로 설정
        normalized_prefix = "raw/seoul_sales/normalized/"
        normalized_objects: List[str] = []

        with tempfile.TemporaryDirectory() as tmp:
            for i, obj in enumerate(files, start=1):
                base = os.path.basename(obj)
                local_in = os.path.join(tmp, base)
                local_out = os.path.join(tmp, f"utf8_{base}")

                print(f"[sales] ({i}/{len(files)}) download: {obj}")
                gcs_hook.download(BUCKET, obj, local_in)

                # utils의 변환 함수 사용
                rows = convert_cp949_csv_to_utf8_stream(
                    input_path=local_in,
                    output_path=local_out,
                    label=f"sales:{base}",
                    progress_every_lines=300_000,
                )
                print(f"[sales] ({i}/{len(files)}) converted: {base} rows={rows}")

                out_obj = f"{normalized_prefix}{base}"
                print(f"[sales] ({i}/{len(files)}) upload: gs://{BUCKET}/{out_obj}")
                
                # utils의 업로드 함수 사용
                gcs_upload_file(gcs_hook, BUCKET, out_obj, local_out)
                normalized_objects.append(out_obj)

        return {
            "normalized_objects": normalized_objects,
            "source_uri": f"gs://{BUCKET}/{normalized_prefix}*.csv",
        }

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
                "sourceUris": ["{{ ti.xcom_pull(task_ids='normalize_to_utf8')['source_uri'] }}"],
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
        # utils의 rowcount 체크 함수 사용
        bq_postcheck_rowcount(
            gcp_conn_id=GCP_CONN_ID,
            location=BQ_LOCATION,
            project=BQ_PROJECT,
            dataset=BQ_DATASET_RAW,
            table=SALES_RAW_TABLE,
            label="seoul_sales",
        )

    m = validate_files()
    m2 = normalize_to_utf8(m)
    m2 >> load_to_bq >> postcheck()
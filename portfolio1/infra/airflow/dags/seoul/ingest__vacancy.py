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
    convert_vacancy_xlsx_to_long_csv,  # long 변환 함수로 교체
    gcs_upload_file,
    bq_postcheck_rowcount,
)


# BQ schema 고정 (long 스키마)
VACANCY_LONG_SCHEMA = [
    {"name": "building_type", "type": "STRING", "mode": "REQUIRED"},
    {"name": "지역별1", "type": "STRING", "mode": "REQUIRED"},
    {"name": "지역별2", "type": "STRING", "mode": "REQUIRED"},
    {"name": "period", "type": "STRING", "mode": "REQUIRED"},
    {"name": "metric", "type": "STRING", "mode": "REQUIRED"},
    {"name": "metric_detail", "type": "STRING", "mode": "REQUIRED"},
    {"name": "value", "type": "FLOAT", "mode": "NULLABLE"},
    {"name": "source_file", "type": "STRING", "mode": "REQUIRED"},
]


with DAG(
    dag_id="ingest__vacancy",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["seoul", "vacancy", "xlsx", "normalize", "bigquery", "raw", "long"],
    max_active_runs=1,
) as dag:

    @task
    def list_xlsx_objects() -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files = list_gcs_objects_with_size(
            gcs_hook, BUCKET, VACANCY_EXTRACTED_PREFIX, suffix=".xlsx"
        )
        validate_min_size(files, MIN_BYTES, label="vacancy")

        xlsx_sorted = sorted([n for (n, _) in files])
        print(f"[vacancy] xlsx files={len(xlsx_sorted)}")
        return {"xlsx_objects": xlsx_sorted}

    @task
    def normalize_xlsx_to_long_csv(meta: dict) -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        xlsx_objects: List[str] = meta["xlsx_objects"]

        normalized_objects: List[str] = []
        total_rows = 0

        with tempfile.TemporaryDirectory() as tmp:
            for i, obj in enumerate(xlsx_objects, start=1):
                base = os.path.basename(obj)          # 예: 매장용빌딩.xlsx
                stem, _ = os.path.splitext(base)      # 예: 매장용빌딩

                local_xlsx = os.path.join(tmp, base)
                local_csv = os.path.join(tmp, f"{stem}_long.csv")

                print(f"[vacancy] ({i}/{len(xlsx_objects)}) download: {obj}")
                gcs_hook.download(BUCKET, obj, local_xlsx)

                # 멀티헤더→flat→ffill→long 변환
                rows = convert_vacancy_xlsx_to_long_csv(
                    input_path=local_xlsx,
                    output_path=local_csv,
                    label=f"vacancy:{base}",
                    building_type=stem,      # 매장용빌딩 / 오피스빌딩
                    source_file=base,
                )
                total_rows += rows

                out_obj = f"{VACANCY_NORMALIZED_PREFIX}{os.path.basename(local_csv)}"
                print(f"[vacancy] ({i}/{len(xlsx_objects)}) upload: gs://{BUCKET}/{out_obj}")
                gcs_upload_file(gcs_hook, BUCKET, out_obj, local_csv)
                normalized_objects.append(out_obj)

        meta["normalized_objects"] = normalized_objects
        meta["source_uri"] = f"gs://{BUCKET}/{VACANCY_NORMALIZED_PREFIX}*_long.csv"
        meta["normalized_total_rows"] = total_rows
        print(f"[vacancy] normalized_total_rows={total_rows}")
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
                "sourceUris": [
                    "{{ ti.xcom_pull(task_ids='normalize_xlsx_to_long_csv')['source_uri'] }}"
                ],
                "sourceFormat": "CSV",
                "skipLeadingRows": 1,
                "encoding": "UTF-8",
                "fieldDelimiter": ",",
                "quote": "\"",
                "allowQuotedNewlines": True,

                # long 스키마는 고정이므로 schema 고정 추천
                "schema": {"fields": VACANCY_LONG_SCHEMA},
                "autodetect": False,

                "createDisposition": "CREATE_IF_NEEDED",
                "writeDisposition": "WRITE_TRUNCATE",

                # long 변환 이후엔 bad record 거의 없어야 정상
                "maxBadRecords": 0,
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
    meta2 = normalize_xlsx_to_long_csv(meta)
    meta2 >> load_to_bq >> postcheck()

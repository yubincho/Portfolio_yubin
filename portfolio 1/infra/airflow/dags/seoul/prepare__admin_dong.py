# dags/seoul/prepare_admin_dong_source.py
from __future__ import annotations

from datetime import datetime
import os
import tempfile

from airflow import DAG
from airflow.decorators import task
from airflow.providers.google.cloud.hooks.gcs import GCSHook

from seoul.config.seoul_config import (
    GCP_CONN_ID,
    BUCKET,
    DEFAULT_ARGS,
    MIN_BYTES,
    ADMIN_DONG_EXTRACTED_PREFIX,
    ADMIN_DONG_SOURCE_URI,
)

from seoul.utils.seoul_dag_utils import (
    list_gcs_objects_with_size,
    validate_min_size,
    convert_xlsx_to_utf8_csv,  # 기존 함수 그대로 사용
    gcs_upload_file,
)

def _gcs_uri_to_object(uri: str) -> str:
    prefix = f"gs://{BUCKET}/"
    if not uri.startswith(prefix):
        raise ValueError(f"Unexpected ADMIN_DONG_SOURCE_URI: {uri}")
    return uri[len(prefix):]


with DAG(
    dag_id="prepare__admin_dong_source",
    start_date=datetime(2026, 2, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["seoul", "admin_dong", "prepare", "xlsx", "normalize", "csv"],
    max_active_runs=1,
) as dag:

    @task
    def prepare_admin_dong_csv() -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)

        files = list_gcs_objects_with_size(
            gcs_hook, BUCKET, ADMIN_DONG_EXTRACTED_PREFIX, suffix=".xlsx"
        )
        validate_min_size(files, MIN_BYTES, label="admin_dong")

        xlsx_objects = sorted([n for (n, _) in files])
        xlsx_obj = xlsx_objects[0]
        base = os.path.basename(xlsx_obj)

        out_obj = _gcs_uri_to_object(ADMIN_DONG_SOURCE_URI)

        with tempfile.TemporaryDirectory() as tmp:
            local_xlsx = os.path.join(tmp, base)
            local_csv = os.path.join(tmp, "admin_dong_code.csv")

            print(f"[admin_dong] download: {xlsx_obj}")
            gcs_hook.download(BUCKET, xlsx_obj, local_xlsx)

            # 기존 함수로 통일 변환
            convert_xlsx_to_utf8_csv(
                input_path=local_xlsx,
                output_path=local_csv,
                label=f"admin_dong:{base}",
            )

            print(f"[admin_dong] upload: gs://{BUCKET}/{out_obj}")
            gcs_upload_file(
                gcs_hook=gcs_hook,
                bucket=BUCKET,
                object_name=out_obj,
                local_path=local_csv,
                mime_type="text/csv",
            )

        return {"xlsx_object": xlsx_obj, "out_object": out_obj}

    prepare_admin_dong_csv()

from __future__ import annotations

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup


# =========================
# 공통 설정
# =========================
GCS_BUCKET = "seoul-commercial-data"

DATASETS = {
    "seoul_sales": {
        "zip_object": "raw/seoul_sales/zip/서울시분기별매출.zip",
        "extracted_prefix": "raw/seoul_sales/extracted",
    },
    "living_population": {
        "zip_object": "raw/living_population/zip/서울시유동인구_스냅샷.zip",
        "extracted_prefix": "raw/living_population/extracted",
    },
    "vacancy": {
        "zip_object": "raw/vacancy/zip/서울시공실률.zip",
        "extracted_prefix": "raw/vacancy/extracted",
    },
}


def make_extract_taskgroup(dag, group_id, zip_object, extracted_prefix):
    """
    ZIP → unzip → GCS extracted
    """
    with TaskGroup(group_id=group_id, dag=dag) as tg:

        BashOperator(
            task_id="extract_and_upload",
            bash_command=r"""
set -euo pipefail

WORK_DIR="/tmp/{{ params.group_id }}"
ZIP_LOCAL="${WORK_DIR}/input.zip"
UNZIP_DIR="${WORK_DIR}/unzipped"

echo "[1/6] Prepare work dir: ${WORK_DIR}"
rm -rf "${WORK_DIR}"
mkdir -p "${WORK_DIR}"
mkdir -p "${UNZIP_DIR}"

echo "[2/6] Download ZIP from GCS"
gsutil cp "gs://{{ params.bucket }}/{{ params.zip_object }}" "${ZIP_LOCAL}"

echo "[3/6] List downloaded ZIP"
ls -lh "${ZIP_LOCAL}"

echo "[4/6] Unzip"
unzip -o "${ZIP_LOCAL}" -d "${UNZIP_DIR}"

echo "[5/6] Show extracted files"
find "${UNZIP_DIR}" -type f | head -20

echo "[6/6] Upload extracted files to GCS"
gsutil -m cp -r "${UNZIP_DIR}/"* \
  "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/"

echo "[DONE] Verify uploaded objects"
gsutil ls "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/" | head -20
""",
            params={
                "bucket": GCS_BUCKET,
                "zip_object": zip_object,
                "extracted_prefix": extracted_prefix,
                "group_id": group_id,
            },
        )

    return tg


# =========================
# DAG 정의
# =========================
with DAG(
    dag_id="extract_all_raw_zips",
    start_date=datetime(2026, 2, 1),
    schedule=None,          # 수동 실행 (테스트 / 배포 초기)
    catchup=False,
    tags=["gcs", "zip", "extract", "raw", "taskgroup"],
) as dag:

    extract_groups = []

    for domain, cfg in DATASETS.items():
        tg = make_extract_taskgroup(
            dag=dag,
            group_id=f"extract_{domain}",
            zip_object=cfg["zip_object"],
            extracted_prefix=cfg["extracted_prefix"],
        )
        extract_groups.append(tg)

    # 병렬 실행 (의존성 없음)
    extract_groups

from __future__ import annotations

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

GCS_BUCKET = "seoul-commercial-data"

DATASETS = {
    "seoul_sales": {
        "zip_object": "raw/seoul_sales/zip/서울시분기별매출.zip",
        "extracted_prefix": "raw/seoul_sales/extracted",
        "mode": "flat",  # 최상위폴더 제거 후 csv만 업로드
    },
    "living_population": {
        "zip_object": "raw/living_population/zip/서울시유동인구_스냅샷.zip",
        "extracted_prefix": "raw/living_population/extracted",
        "mode": "year_dirs",  # 2023/2024/2025 유지
    },
    "vacancy": {
        "zip_object": "raw/vacancy/zip/서울시공실률.zip",
        "extracted_prefix": "raw/vacancy/extracted",
        "mode": "flat",
    },
}

def make_extract_taskgroup(dag, group_id, zip_object, extracted_prefix, mode: str):
    with TaskGroup(group_id=group_id, dag=dag) as tg:

        BashOperator(
            task_id="extract_and_upload",
            bash_command=r"""
set -euo pipefail

WORK_DIR="/tmp/{{ params.group_id }}"
ZIP_LOCAL="${WORK_DIR}/input.zip"
UNZIP_DIR="${WORK_DIR}/unzipped"

echo "[1/7] Prepare work dir: ${WORK_DIR}"
rm -rf "${WORK_DIR}"
mkdir -p "${UNZIP_DIR}"

echo "[2/7] Download ZIP from GCS"
gsutil cp "gs://{{ params.bucket }}/{{ params.zip_object }}" "${ZIP_LOCAL}"

echo "[3/7] Unzip"
unzip -o "${ZIP_LOCAL}" -d "${UNZIP_DIR}"

echo "[4/7] Detect root folder (top-level folder inside zip)"
ROOT_DIR="$(find "${UNZIP_DIR}" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [ -z "${ROOT_DIR}" ]; then
  echo "No root folder found under ${UNZIP_DIR}"
  exit 1
fi
echo "ROOT_DIR=${ROOT_DIR}"
find "${ROOT_DIR}" -type f | head -20

echo "[5/7] Upload extracted files to GCS (mode={{ params.mode }})"
if [ "{{ params.mode }}" = "flat" ]; then
  # 최상위 폴더 아래의 CSV만 extracted/로 올림
  gsutil -m cp "${ROOT_DIR}/"*.csv "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/"
elif [ "{{ params.mode }}" = "year_dirs" ]; then
  # ROOT_DIR/2023|2024|2025 폴더를 extracted/ 아래로 유지해서 업로드
  for y in 2023 2024 2025; do
    if [ -d "${ROOT_DIR}/${y}" ]; then
      gsutil -m cp "${ROOT_DIR}/${y}/"*.csv "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/${y}/"
    else
      echo "WARN: missing year dir ${ROOT_DIR}/${y}"
    fi
  done
else
  echo "Unknown mode={{ params.mode }}"
  exit 1
fi

echo "[6/7] Verify uploaded objects"
gsutil ls "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/" | head -20

echo "[7/7] Done"
""",
            params={
                "bucket": GCS_BUCKET,
                "zip_object": zip_object,
                "extracted_prefix": extracted_prefix,
                "group_id": group_id,
                "mode": mode,
            },
        )

    return tg


with DAG(
    dag_id="seoul_extract_all_raw_zips",
    start_date=datetime(2026, 2, 1),
    schedule=None,
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
            mode=cfg["mode"],
        )
        extract_groups.append(tg)

    extract_groups

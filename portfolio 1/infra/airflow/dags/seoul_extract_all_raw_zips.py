from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup

GCS_BUCKET = "seoul-commercial-data"

DATASETS = {
    "seoul_sales": {
        "zip_object": "raw/seoul_sales/zip/서울시분기별매출.zip",
        "extracted_prefix": "raw/seoul_sales/extracted",
        "mode": "flat",
    },
    "living_population": {
        "zip_object": "raw/living_population/zip/서울시유동인구_스냅샷.zip",
        "extracted_prefix": "raw/living_population/extracted",
        "mode": "year_dirs",
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

echo "[4/7] Detect root folder"
ROOT_DIR="$(find "${UNZIP_DIR}" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [ -z "${ROOT_DIR}" ]; then
  echo "No root folder found under ${UNZIP_DIR}"
  exit 1
fi

echo "ROOT_DIR=${ROOT_DIR}"
find "${ROOT_DIR}" -type f | head -20

echo "[5/7] Upload extracted files"

if [ "{{ params.mode }}" = "flat" ]; then
  shopt -s nullglob
  files=("${ROOT_DIR}/"*.csv "${ROOT_DIR}/"*.xlsx "${ROOT_DIR}/"*.xls)

  if [ ${#files[@]} -eq 0 ]; then
    echo "No csv/xlsx/xls files found"
    exit 1
  fi

  gsutil -m cp "${files[@]}" \
    "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/"

elif [ "{{ params.mode }}" = "year_dirs" ]; then
  for y in 2023 2024 2025; do
    if [ -d "${ROOT_DIR}/${y}" ]; then
      shopt -s nullglob
      year_files=("${ROOT_DIR}/${y}/"*.csv \
                  "${ROOT_DIR}/${y}/"*.xlsx \
                  "${ROOT_DIR}/${y}/"*.xls)

      if [ ${#year_files[@]} -gt 0 ]; then
        gsutil -m cp "${year_files[@]}" \
          "gs://{{ params.bucket }}/{{ params.extracted_prefix }}/${y}/"
      fi
    fi
  done
fi

echo "[6/7] Verify"
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
    tags=["gcs", "zip", "extract", "raw"],
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=3),
    },
) as dag:

    # TaskGroup 생성
    tg_seoul_sales = make_extract_taskgroup(
        dag,
        "extract_seoul_sales",
        DATASETS["seoul_sales"]["zip_object"],
        DATASETS["seoul_sales"]["extracted_prefix"],
        DATASETS["seoul_sales"]["mode"],
    )

    tg_living_population = make_extract_taskgroup(
        dag,
        "extract_living_population",
        DATASETS["living_population"]["zip_object"],
        DATASETS["living_population"]["extracted_prefix"],
        DATASETS["living_population"]["mode"],
    )

    tg_vacancy = make_extract_taskgroup(
        dag,
        "extract_vacancy",
        DATASETS["vacancy"]["zip_object"],
        DATASETS["vacancy"]["extracted_prefix"],
        DATASETS["vacancy"]["mode"],
    )

    # 순차 실행 (여기가 핵심)
    tg_seoul_sales >> tg_living_population >> tg_vacancy

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple
import os
import re
import tempfile
import io

from airflow import DAG
from airflow.decorators import task
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook


# =========================
# 설정
# =========================
GCP_CONN_ID = "google_cloud_default"
BUCKET = "seoul-commercial-data"

BQ_PROJECT = "smart-paratext-486618-v8"
BQ_DATASET = "raw"
BQ_LOCATION = "asia-northeast3"

BASE_EXTRACTED = "raw/living_population/extracted/서울시유동인구_스냅샷/"
BASE_NORMALIZED = "raw/living_population/normalized/서울시유동인구_스냅샷/"

DEFAULT_ARGS = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}

MIN_BYTES = 1024  # 1KB 미만이면 깨진 파일로 간주


# =========================
# 유틸
# =========================
def normalize_col(col: str) -> str:
    """
    BigQuery 컬럼명 안전화: 영문/숫자/언더스코어만
    """
    s = re.sub(r"[^\w]+", "_", str(col))
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "col"
    if s[0].isdigit():
        s = "c_" + s
    return s


def list_csv_with_size(gcs_hook: GCSHook, prefix: str) -> List[Tuple[str, int]]:
    client = gcs_hook.get_conn()
    out = []
    for blob in client.list_blobs(BUCKET, prefix=prefix):
        name = blob.name
        if name.endswith(".csv") and not name.endswith("/"):
            out.append((name, int(blob.size or 0)))
    return out


def convert_cp949_csv_to_utf8_stream(
    input_path: str,
    output_path: str,
    label: str,
    progress_every_lines: int = 300_000,
) -> int:
    """
    대용량 CSV용 스트리밍 변환:
    - input: cp949(또는 유사) CSV
    - output: utf-8 CSV
    - 헤더는 컬럼명 정규화해서 출력
    - 데이터는 라인 단위로 그대로 복사(메모리 거의 사용 안 함)
    """
    rows = 0

    with open(input_path, "rb") as f_in, open(output_path, "w", encoding="utf-8", newline="") as f_out:
        # cp949 텍스트 스트림 (에러는 replace로 흡수)
        text_in = io.TextIOWrapper(f_in, encoding="cp949", errors="replace", newline="")

        # 1) 헤더
        header = text_in.readline()
        if not header:
            raise ValueError(f"[{label}] empty file (no header)")

        cols = [c.strip().strip('"') for c in header.strip().split(",")]
        norm_cols = [normalize_col(c) for c in cols]
        f_out.write(",".join(norm_cols) + "\n")

        # 2) 데이터
        for line in text_in:
            if line.strip():
                f_out.write(line)
                rows += 1

            if rows > 0 and rows % progress_every_lines == 0:
                print(f"[{label}] converted rows={rows}")

    if rows == 0:
        raise ValueError(f"[{label}] output has 0 data rows (header-only?)")

    return rows


# =========================
# DAG
# =========================
with DAG(
    dag_id="load__raw__livingpop__year_test_three",
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

        extracted_prefix = f"{BASE_EXTRACTED}{year}/"
        normalized_prefix = f"{BASE_NORMALIZED}{year}/"
        table_id = f"living_population_raw_{year}"  # 연도별 raw 테이블

        return {
            "year": year,
            "extracted_prefix": extracted_prefix,
            "normalized_prefix": normalized_prefix,
            "table_id": table_id,
        }

    @task
    def list_and_validate(meta: dict) -> dict:
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        files = list_csv_with_size(gcs_hook, meta["extracted_prefix"])

        print(f"[livingpop] gs://{BUCKET}/{meta['extracted_prefix']} files={len(files)}")
        if not files:
            raise FileNotFoundError("No extracted CSV files found")

        tiny = [(n, s) for (n, s) in files if s < MIN_BYTES]
        if tiny:
            for n, s in tiny[:20]:
                print(f"[livingpop] tiny file: {n} size={s}")
            raise ValueError(f"Found {len(tiny)} tiny CSV files (<{MIN_BYTES} bytes). unzip may be broken.")

        # 안정성을 위해 정렬(항상 같은 순서로 처리)
        files_sorted = sorted([n for (n, _) in files])
        meta["files"] = files_sorted
        return meta

    @task
    def normalize_to_utf8(meta: dict) -> dict:
        """
        extracted(cp949) -> normalized(utf-8) 스트리밍 변환
        - pandas 사용 안 함 (OOM/좀비 방지)
        - 헤더 컬럼명은 정규화
        """
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

                # 스트리밍 변환
                rows = convert_cp949_csv_to_utf8_stream(
                    input_path=local_in,
                    output_path=local_out,
                    label=f"livingpop:{year}:{base}",
                    progress_every_lines=300_000,
                )
                print(f"[livingpop] ({i}/{len(files)}) converted: {base} rows={rows}")

                out_obj = f"{normalized_prefix}{base}"
                print(f"[livingpop] ({i}/{len(files)}) upload: gs://{BUCKET}/{out_obj}")
                gcs_hook.upload(BUCKET, out_obj, local_out, mime_type="text/csv")
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
                    "datasetId": BQ_DATASET,
                    "tableId": "{{ ti.xcom_pull(task_ids='resolve_year')['table_id'] }}",
                },
                "sourceUris": [
                    "{{ ti.xcom_pull(task_ids='normalize_to_utf8')['source_uri'] }}"
                ],
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

    # 여기만 변경됨: pandas_gbq 경로(get_pandas_df) 제거
    @task
    def postcheck(meta: dict):
        bq = BigQueryHook(gcp_conn_id=GCP_CONN_ID, location=BQ_LOCATION)
        table_id = meta["table_id"]
        sql = f"SELECT COUNT(*) AS cnt FROM `{BQ_PROJECT}.{BQ_DATASET}.{table_id}`"

        # pandas_gbq(read_gbq) 대신 BigQuery client로 직접 실행
        client = bq.get_client(project_id=BQ_PROJECT, location=BQ_LOCATION)
        job = client.query(sql)
        rows = list(job.result())
        cnt = int(rows[0]["cnt"])

        print(f"[livingpop] BQ rowcount={cnt}")
        if cnt == 0:
            raise ValueError("Loaded rowcount is 0 (unexpected). Check normalized files.")

    meta = resolve_year()
    meta2 = list_and_validate(meta)
    meta3 = normalize_to_utf8(meta2)
    meta3 >> load_to_bq >> postcheck(meta3)

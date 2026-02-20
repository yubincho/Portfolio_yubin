# update 2026 02 18 
# seoul_dag_utils.py
from __future__ import annotations

import os
import re
import csv
import io
from typing import List, Tuple, Optional

import pandas as pd
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook


def normalize_column_name(col: str) -> str:
    """
    BigQuery 컬럼명 안전화: 영문/숫자/언더스코어만
    - 공백/특수문자 -> _
    - 연속 _ 정리
    - 숫자로 시작하면 c_ prefix
    """
    s = re.sub(r"[^\w]+", "_", str(col))
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "col"
    if s[0].isdigit():
        s = "c_" + s
    return s


def list_gcs_objects_with_size(
    gcs_hook: GCSHook,
    bucket: str,
    prefix: str,
    suffix: Optional[str] = None,
) -> List[Tuple[str, int]]:
    """
    gs://bucket/prefix 아래의 object 목록을 (name, size)로 반환
    suffix가 있으면 해당 확장자만 필터
    """
    client = gcs_hook.get_conn()
    out: List[Tuple[str, int]] = []
    for blob in client.list_blobs(bucket, prefix=prefix):
        name = blob.name
        if name.endswith("/"):
            continue
        if suffix and not name.endswith(suffix):
            continue
        out.append((name, int(blob.size or 0)))
    return out


def validate_min_size(
    files_with_size: List[Tuple[str, int]],
    min_bytes: int,
    label: str,
) -> None:
    """
    파일 존재/최소크기 체크
    """
    if not files_with_size:
        raise FileNotFoundError(f"[{label}] no files found")

    tiny = [(n, s) for (n, s) in files_with_size if s < min_bytes]
    if tiny:
        for n, s in tiny[:20]:
            print(f"[{label}] tiny file: {n} size={s}")
        raise ValueError(f"[{label}] Found {len(tiny)} tiny files (<{min_bytes} bytes)")


def convert_cp949_csv_to_utf8_stream(
    input_path: str,
    output_path: str,
    label: str,
    progress_every_lines: int = 300_000,
) -> int:
    """
    큰 CSV(cp949)를 줄 단위로 읽어서 UTF-8 CSV로 변환
    - 헤더를 normalize_column_name 처리
    - 데이터 로우가 0이면 에러
    """
    rows = 0
    with open(input_path, "rb") as f_in, open(output_path, "w", encoding="utf-8", newline="") as f_out:
        text_in = io.TextIOWrapper(f_in, encoding="cp949", errors="replace", newline="")

        header = text_in.readline()
        if not header:
            raise ValueError(f"[{label}] empty file (no header)")

        cols = [c.strip().strip('"') for c in header.strip().split(",")]
        norm_cols = [normalize_column_name(c) for c in cols]
        f_out.write(",".join(norm_cols) + "\n")

        for line in text_in:
            if line.strip():
                f_out.write(line)
                rows += 1
            if rows > 0 and rows % progress_every_lines == 0:
                print(f"[{label}] converted rows={rows}")

    if rows == 0:
        raise ValueError(f"[{label}] output has 0 data rows (header-only?)")

    return rows


def convert_xlsx_to_utf8_csv(
    input_path: str,
    output_path: str,
    label: str,
    quoting: int = csv.QUOTE_NONNUMERIC,  # ← 변경
) -> None:
    """
    XLSX를 UTF-8 CSV로 변환
    - dtype=str로 타입 혼합 방지
    - QUOTE_ALL로 줄바꿈/콤마 포함 셀 안전하게 처리
    - 빈 행 제거 / NaN -> '' 처리
    """
    df = pd.read_excel(
        input_path,
        engine="openpyxl",
        sheet_name=0,
        dtype=str,
    )

    if df.shape[0] == 0:
        raise ValueError(f"[{label}] XLSX has 0 rows: {input_path}")

    df.columns = [normalize_column_name(c) for c in df.columns]
    df = df.dropna(how="all").fillna("")

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
        quoting=quoting,
        lineterminator="\n",
        escapechar='\\',  # ← 추가: 이스케이프 문자 명시
    )
    print(f"[{label}] ✓ XLSX->CSV rows={len(df)} cols={len(df.columns)}")


# vacancy 엑셀 -> csv 변환용 함수 
def convert_vacancy_xlsx_to_utf8_csv(
    input_path: str,
    output_path: str,
    label: str,
) -> None:
    """
    [vacancy 전용]
    XLSX를 UTF-8 CSV로 변환 + '추가 헤더 행' 제거

    vacancy 엑셀(매장용빌딩/오피스빌딩)은
    컬럼 헤더 아래에 "지역별(1), 지역별(2), ..." 같은
    다단 헤더가 1~3줄 더 들어있는 경우가 있어,
    그대로 CSV로 만들면 BigQuery에서 컬럼 수 불일치로 실패함.

    처리:
    - dtype=str로 타입 혼합 방지
    - 빈 행 제거 / NaN -> '' 처리
    - 헤더 아래 연속된 '추가 헤더 행' 제거
    - QUOTE_ALL + escapechar로 BigQuery 로드 안정화
    """
    df = pd.read_excel(
        input_path,
        engine="openpyxl",
        sheet_name=0,
        dtype=str,
        header=0,  # 첫 행을 컬럼으로 사용
    )

    if df.shape[0] == 0:
        raise ValueError(f"[{label}] XLSX has 0 rows: {input_path}")

    # 빈 행 제거 + NaN 제거
    df = df.dropna(how="all").fillna("")

    # (중요) vacancy는 헤더 아래에 다단 헤더(지역별(1), 지역별(2) 등)가 추가로 들어있음
    def _is_extra_header_row(row) -> bool:
        # 첫 두 컬럼 기준으로 패턴 감지
        first = str(row.iloc[0]).strip() if len(row) > 0 else ""
        second = str(row.iloc[1]).strip() if len(row) > 1 else ""
        # 예: "지역별(1)", "지역별(2)" / "지역별(1)", "지역별(2)" 등
        if "지역별" in first and ("지역별" in second or second.endswith("(2)")):
            return True
        return False

    # 앞부분에서 연속되는 추가 헤더 행 제거(방어적으로 최대 5줄)
    drop_idx = []
    for i in range(min(5, len(df))):
        if _is_extra_header_row(df.iloc[i]):
            drop_idx.append(df.index[i])
        else:
            break

    if drop_idx:
        print(f"[{label}] drop extra header rows: {len(drop_idx)}")
        df = df.drop(index=drop_idx)

    if df.shape[0] == 0:
        raise ValueError(f"[{label}] after dropping extra header rows, 0 data rows")

    # 컬럼명 정규화
    df.columns = [normalize_column_name(c) for c in df.columns]

    # 줄바꿈 정규화(혹시 섞여있으면 BigQuery에서 파싱 꼬일 수 있음)
    df = df.replace({"\r\n": "\n", "\r": "\n"}, regex=True)

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_ALL,  # vacancy는 안전하게 ALL 권장
        lineterminator="\n",
        escapechar="\\",
        doublequote=True,
    )

    print(f"[{label}] ✓ vacancy XLSX->CSV rows={len(df)} cols={len(df.columns)} (QUOTE_ALL)")


def bq_postcheck_rowcount(
    gcp_conn_id: str,
    location: str,
    project: str,
    dataset: str,
    table: str,
    label: str,
) -> int:
    """
    BigQuery 테이블 rowcount 체크 (0이면 에러)
    """
    bq = BigQueryHook(gcp_conn_id=gcp_conn_id, location=location)
    client = bq.get_client(project_id=project, location=location)
    rows = list(client.query(f"SELECT COUNT(*) AS cnt FROM `{project}.{dataset}.{table}`").result())
    cnt = int(rows[0]["cnt"])
    print(f"[{label}] BQ rowcount={cnt}")
    if cnt == 0:
        raise ValueError(f"[{label}] Loaded rowcount is 0")
    return cnt


def gcs_upload_file(
    gcs_hook: GCSHook,
    bucket: str,
    object_name: str,
    local_path: str,
    mime_type: str = "text/csv",
) -> None:
    gcs_hook.upload(bucket, object_name, local_path, mime_type=mime_type)

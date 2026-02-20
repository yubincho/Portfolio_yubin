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


def _clean_text(s: str) -> str:
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
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


# =========================================================
# Vacancy 전용: XLSX(멀티헤더/병합셀) -> LONG CSV
# =========================================================
def _flatten_vacancy_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    MultiIndex(3레벨) 컬럼을 flat으로 변환
    - ('지역별(1)' or '구분별(1)') -> 지역별1
    - ('지역별(2)' or '구분별(2)') -> 지역별2
    - 나머지 -> "기간_지표_세부" 형태
    """
    if not isinstance(df.columns, pd.MultiIndex):
        return df

    cols_df = pd.DataFrame(df.columns.tolist()).ffill(axis=0).ffill(axis=1)

    new_cols: List[str] = []
    for a, b, c in cols_df.itertuples(index=False):
        a = _clean_text(a)
        b = _clean_text(b)
        c = _clean_text(c)

        if a in ("지역별(1)", "구분별(1)"):
            new_cols.append("지역별1")
        elif a in ("지역별(2)", "구분별(2)"):
            new_cols.append("지역별2")
        else:
            parts = [p for p in (a, b, c) if p and p.lower() not in ("nan", "none")]
            new_cols.append("_".join(parts))

    out = df.copy()
    out.columns = new_cols
    return out


def _to_vacancy_long(df_wide: pd.DataFrame) -> pd.DataFrame:
    id_vars = ["지역별1", "지역별2"]
    value_vars = [c for c in df_wide.columns if c not in id_vars]

    long = df_wide.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="col",
        value_name="value",
    )

    # col 예: "2023 1/4_임대료 (천원/㎡)_소계"
    parts = long["col"].astype(str).str.split("_", n=2, expand=True)
    if parts.shape[1] < 3:
        raise ValueError("[vacancy] column split failed: expected 'period_metric_detail'")

    long["period"] = parts[0].astype(str).str.strip()
    long["metric"] = parts[1].astype(str).str.strip()
    long["metric_detail"] = parts[2].astype(str).str.strip()
    long = long.drop(columns=["col"])

    # value 숫자화
    long["value"] = (long["value"].astype(str)
                     .str.replace(",", "", regex=False)
                     .str.strip()
                     .replace({"nan": np.nan, "": np.nan}))
    long["value"] = pd.to_numeric(long["value"], errors="coerce")

    # 키 정리
    long["지역별1"] = long["지역별1"].astype(str).str.strip()
    long["지역별2"] = long["지역별2"].astype(str).str.strip()

    # 핵심 키 결측 제거
    long = long.dropna(subset=["지역별1", "지역별2", "period", "metric", "metric_detail"])

    return long


def convert_vacancy_xlsx_to_long_csv(
    input_path: str,
    output_path: str,
    label: str,
    building_type: str,
    source_file: str,
) -> int:
    """
    [vacancy 전용]
    XLSX(멀티헤더) -> flat -> ffill -> long -> CSV(QUOTE_ALL) 저장
    반환: long row count
    """
    # 멀티헤더 3줄을 통째로 읽는다 (핵심!)
    df = pd.read_excel(
        input_path,
        engine="openpyxl",
        sheet_name=0,
        header=[0, 1, 2],
        dtype=str,
    )

    if df.shape[0] == 0:
        raise ValueError(f"[{label}] XLSX has 0 rows: {input_path}")

    df = _flatten_vacancy_columns(df)

    if "지역별1" not in df.columns or "지역별2" not in df.columns:
        print(f"[{label}] columns sample:", list(df.columns)[:12])
        raise ValueError(f"[{label}] 지역별1/지역별2 컬럼 생성 실패. 헤더 구조 확인 필요.")

    # 상위 지역 ffill (병합셀 대응)
    df["지역별1"] = (df["지역별1"].astype(str).str.strip()
                    .replace({"nan": np.nan, "": np.nan})
                    .ffill())
    df["지역별2"] = (df["지역별2"].astype(str).str.strip()
                    .replace({"nan": np.nan, "": np.nan}))

    # 빈 행 제거
    df = df.dropna(how="all")

    long = _to_vacancy_long(df)

    # 메타 컬럼 추가 (BQ에 같이 적재)
    long["building_type"] = building_type
    long["source_file"] = source_file

    # 컬럼 순서 고정
    long = long[["building_type", "지역별1", "지역별2", "period", "metric", "metric_detail", "value", "source_file"]]

    # BigQuery-safe CSV
    long.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_ALL,
        escapechar="\\",
        doublequote=True,
        lineterminator="\n",
    )

    print(f"[{label}] ✓ Vacancy XLSX→LONG CSV rows={len(long)} cols={len(long.columns)}")
    return int(len(long))


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

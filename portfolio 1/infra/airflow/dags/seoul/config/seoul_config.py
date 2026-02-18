# dags/seoul/config/seoul_config.py
from __future__ import annotations
from datetime import timedelta

# ===== Airflow / GCP =====
GCP_CONN_ID = "google_cloud_default"

# ===== Storage =====
BUCKET = "seoul-commercial-data"

# ===== BigQuery =====
BQ_PROJECT = "smart-paratext-486618-v8"
BQ_DATASET_RAW = "raw"
BQ_DATASET_MART = "mart"
BQ_LOCATION = "asia-northeast3"

# ===== Default args =====
DEFAULT_ARGS = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}

# ===== Validation =====
MIN_BYTES = 1024

# ===== GCS Prefixes =====
# living population
LIVINGPOP_EXTRACTED_BASE = "raw/living_population/extracted/서울시유동인구_스냅샷/"
LIVINGPOP_NORMALIZED_BASE = "raw/living_population/normalized/서울시유동인구_스냅샷/"

# sales
SALES_EXTRACTED_PREFIX = "raw/seoul_sales/extracted/"

# vacancy
VACANCY_EXTRACTED_PREFIX = "raw/vacancy/extracted/"
VACANCY_NORMALIZED_PREFIX = "raw/vacancy/normalized/"

# admin dong (dim)
ADMIN_DONG_SOURCE_URI = "gs://seoul-commercial-data/raw/admin_dong/admin_dong_code.txt"
ADMIN_DONG_RAW_TABLE = "admin_dong_raw"
ADMIN_DONG_DIM_TABLE = "dim_admin_dong"

# ===== Table IDs =====
SALES_RAW_TABLE = "seoul_sales_raw"
VACANCY_RAW_TABLE = "vacancy_raw"

def livingpop_table_id(year: str) -> str:
    return f"living_population_raw_{year}"

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="BigQuery Connection Test", layout="wide")

PROJECT_ID = "smart-paratext-486618-v8"

# ---------------------------
# BigQuery helper
# ---------------------------
def get_bq_client() -> bigquery.Client:
    """
    Creates a BigQuery client using Streamlit secrets.
    Expected secrets key:
      [gcp_service_account] (TOML table)
    """
    if "gcp_service_account" not in st.secrets:
        st.error("Streamlit Secrets에 [gcp_service_account]가 없습니다. Settings → Secrets를 확인하세요.")
        st.stop()

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=creds, project=PROJECT_ID)

@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    client = get_bq_client()
    return client.query(sql).to_dataframe()

# ---------------------------
# UI
# ---------------------------
st.title("✅ BigQuery 연결 테스트")
st.caption(f"Target project_id: `{PROJECT_ID}`")

# 1) 가장 안전한 테스트: SELECT 1
st.subheader("1) 기본 쿼리 테스트 (SELECT 1)")
try:
    df_ok = run_query("SELECT 1 AS ok")
    st.success("SELECT 1 성공 ✅ (인증 + bigquery.jobs.create 권한 정상)")
    st.dataframe(df_ok, use_container_width=True)
except Exception as e:
    st.error("SELECT 1 실패 ❌")
    st.exception(e)
    st.stop()

# 2) (선택) mart 테이블 조회 테스트
st.subheader("2) mart 테이블 조회 테스트 (선택)")
st.write("아래에 네 mart 테이블 전체 경로를 입력하고 테스트할 수 있어.")
table_path = st.text_input(
    "예: smart-paratext-486618-v8.mart.mart_sales_sigungu_quarter",
    value=f"{PROJECT_ID}.mart.mart_sales_sigungu_quarter",
)

limit = st.number_input("LIMIT", min_value=1, max_value=1000, value=5, step=1)

if st.button("테이블 조회 테스트 실행"):
    sql_table = f"SELECT * FROM `{table_path}` LIMIT {int(limit)}"
    try:
        df_sample = run_query(sql_table)
        st.success("테이블 조회 성공 ✅")
        st.dataframe(df_sample, use_container_width=True)
    except Exception as e:
        st.error("테이블 조회 실패 ❌")
        st.exception(e)

# 3) (디버그) 어떤 Secrets 키가 잡혔는지 확인 (민감정보 노출 X)
st.subheader("3) Secrets 확인 (민감정보는 숨김)")
sa = dict(st.secrets["gcp_service_account"])
# 민감한 값 마스킹
for k in ["private_key", "private_key_id", "client_id"]:
    if k in sa:
        sa[k] = "***hidden***"
st.json(sa)
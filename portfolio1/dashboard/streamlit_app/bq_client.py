from google.oauth2 import service_account
from google.cloud import bigquery
import streamlit as st
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "smart-paratext-486618-v8")
LOCATION   = os.getenv("BQ_LOCATION", "asia-northeast3")

@st.cache_resource
def get_bq_client() -> bigquery.Client:
    # 1) Streamlit secrets에 서비스계정이 있으면 그걸 최우선 사용
    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT_ID, credentials=creds, location=LOCATION)

    # 2) 없으면 ADC(로컬 gcloud auth application-default login 등) 시도
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)
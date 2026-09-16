<br>


# 조유빈(Yubin Cho) | Data Engineer Portfolio 🤗
웹 개발 경력을 바탕으로 데이터 엔지니어링으로 전환 중입니다.

GCP 환경에서 Airflow로 오케스트레이션한 ELT 데이터 파이프라인을
설계·구현합니다.

**핵심 기술 스택**
GCP (GCS, BigQuery) · Apache Airflow · dbt · Python · SQL · Streamlit

---
<br>

## Portfolio 1 — 서울시 상권 분석 데이터 파이프라인

GCS → Airflow → BigQuery → dbt → Data Mart 로 이어지는
엔드투엔드 ELT 파이프라인을 구축했습니다.

- **수집/적재**: 원천 데이터를 GCS에 적재하고, Airflow DAG로 BigQuery까지 자동 적재
- **오케스트레이션**: Airflow DAG 2종으로 수집·적재 파이프라인 스케줄링/운영
- **변환(ELT)**: dbt로 Raw → Staging → Mart 3계층 데이터 모델링
- **데이터 마트**: mart_sales_dong_quarter 등 분석용 마트 테이블 설계
- **시각화**: Streamlit 대시보드 https://seoul-commercial-insight.streamlit.app/

➡️ 자세한 내용은 [`portfolio1/`](https://github.com/yubincho/Portfolio_yubin/tree/main/portfolio1) 폴더에서 확인할 수 있습니다.

<br><br>

## Portfolio 2 — BitAnalyzer: 개인 암호화폐 거래 분석 시스템

빗썸 API로 개인 거래 데이터를 수집하고, 거래 내역을 정제·적재하는
데이터 파이프라인을 구축한 프로젝트입니다.

Java Spring 백엔드와 Python 기반 분석 서비스를 분리한
세미 마이크로서비스 구조로 설계했습니다.

- **데이터 수집**: 빗썸 API 연동으로 개인 거래·자산 데이터 수집
- **데이터 정제**: 거래 내역 파일을 정제·표준화하여 분석용 데이터로 가공
- **아키텍처**: Spring(백엔드) + Python(분석) 세미 마이크로서비스 분리
- **데이터 모델링**: 거래 데이터 저장을 위한 테이블 설계

➡️ 자세한 내용은 [`portfolio2/`](https://github.com/yubincho/Portfolio_yubin/tree/main/portfolio2) 폴더에서 확인할 수 있습니다.

<br><br>

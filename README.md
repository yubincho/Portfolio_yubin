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

➡️ 자세한 내용은 [`portfolio1/`](https://github.com/yubincho/Portfolio_yubin/tree/main/portfolio%201) 폴더에서 확인할 수 있습니다.

<br><br>

## Portfolio 2 — 서울시 상권 분석 (ML/DL 모델링 확장)

Portfolio 1에서 구축한 **행정동×분기 단위 통합 데이터 마트(유동인구 × 매출 × 공실률)**를 학습 데이터로 활용하여,  
머신러닝/딥러닝 기반으로 **상권 성과 예측 및 리스크 탐지 모델**까지 확장할 예정입니다.


➡️ 프로젝트는 추후 `portfolio2/` 폴더에 정리할 예정입니다.

<br><br>



<img width="180" height="190" alt="서울 지형 2" src="https://github.com/user-attachments/assets/13b58896-f5ed-419b-a178-ed05961222bf" />


---

# 서울시 상권 분석 (유동인구 × 매출)
<p align="center"> <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>  →  <img src="https://img.shields.io/badge/Google_Cloud_Storage-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white"/>  →  <img src="https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white"/>  →  <img src="https://img.shields.io/badge/BigQuery-669DF6?style=for-the-badge&logo=googlebigquery&logoColor=white"/>  →  <img src="https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white"/>  →  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/> </p>

<p align="center"> <a href="https://seoul-commercial-insight.streamlit.app/" target="_blank"> <img src="https://img.shields.io/badge/🚀_Live_Demo-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit App"/> </a>   <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white"/> </p>

<br>

## 1. 프로젝트 개요

서울시 상권 데이터를 활용하여 **상권 성장률과 유동인구 변화를 분석하고 유망 상권을 탐색하는 데이터 프로젝트**입니다.

단순 분석에 그치지 않고,

**데이터 파이프라인 구축 → 데이터 모델링 → 분석 → 대시보드 시각화** 까지 전체 데이터 흐름을 직접 구현하는 것을 목표로 합니다.

분석 결과는 **Streamlit 대시보드 ([바로가기](https://seoul-commercial-insight.streamlit.app/))** 를 통해 인터랙티브하게 탐색할 수 있습니다.

---

### 핵심 질문
- 서울에서 **성장하는 상권**은 어디인가? 
- **매출 성장과 유동인구 변화**는 어떤 관계가 있는가?
- **최근 떠오르는 상권 (Hot Area)** 은 어디인가?
- **시간대 · 성별 · 요일**에 따라 소비 패턴은 어떻게 다른가?

<br>

💡 머신러닝 / 딥러닝은 **의도적으로 제외**했습니다.

본 프로젝트는 **데이터 웨어하우스 설계 · 정합성 확보 · 집계 로직 설계**에 집중하며,  
**ELT 기반 데이터 모델링만으로도 충분히 설명 가능한 분석 인사이트 도출**을 목표로 합니다.

## Presentation

프로젝트 전체 구조와 분석 결과는 아래 발표 자료에서 확인할 수 있습니다.

👉 [서울 상권 분석 프로젝트 발표 자료](./docs/서울_상권_데이터파이프라인.pdf)

<br>
<br>

## 2. 기술 스택

| 영역 | 기술 | 역할 |
|---|---|---|
| Orchestration | **Apache Airflow (Cloud Composer)** | DAG 기반 파이프라인 자동화 |
| Data Lake | **Google Cloud Storage (GCS)** | 원천 파일(ZIP) 적재 및 Raw 파일 보관 |
| Data Warehouse | **Google BigQuery** | Raw / Staging / Mart 레이어 관리 |
| Transformation | **dbt** | SQL 기반 ELT 변환 및 집계 |
| Language | **Python** | 데이터 수집 · 사전 검증 · 보조 전처리 |
| Visualization | **Streamlit** | 인터랙티브 대시보드 |
| Version Control | **GitHub** | 코드 관리 및 문서화 |

<br>
<br>

## 3. 데이터 아키텍처

프로젝트는 **Raw → Staging → Mart** 3-레이어 구조로 설계되었습니다.
```
공공데이터 (ZIP)
      │  업로드
      ▼
Google Cloud Storage (GCS)
      │  Airflow DAG 1: 압축 해제 → GCS 재적재
      │  Airflow DAG 2: GCS Raw → BigQuery 적재
      ▼
BigQuery – Raw Layer
      │  dbt: 컬럼 정리·타입 변환·중복 제거
      ▼
BigQuery – Staging Layer
      │  dbt: 행정동 × 분기 집계·지표 생성
      ▼
BigQuery – Mart Layer
      │
      ▼
Streamlit Dashboard
```
<br>
<img width="3209" height="1369" alt="architecture_v4" src="https://github.com/user-attachments/assets/dfc17a01-67b5-45e4-85b9-840968745604" />


<br>

### 레이어별 역할

| 레이어 | 역할 |
|---|---|
| Raw | GCS 원천 데이터를 BigQuery에 그대로 로딩. 원본 보존 및 재처리 가능성 확보 |
| Staging | 컬럼 정리 · 타입 변환 · 행정동 코드 정합성 확보 · 결측치 및 중복 처리. **비즈니스 집계 로직 미포함** |
| Mart | 행정동 × 분기 단위 집계. 분석 · 시각화에 직접 사용 가능한 지표 제공 |

<br>
<br>

## 4. 데이터셋

서울시에서 제공하는 데이터를 활용했습니다.

| 데이터 | 세부 항목 |
|---|---|
| 상권 매출 | 분기별 매출, 업종별 매출, 시간대별 매출, 성별 매출 |
| 유동인구 | 행정동 기준 유동인구, 시간대별 인구 |

데이터는 **행정동 단위로 정규화 후 시군구 단위로 집계**하여 분석했습니다.

<br>
<br>

## 5. 데이터 모델링
- 프로젝트 테이블 구성 (Raw → Staging → Analytics): [레이어별_테이블구성.pdf](./portfolio%201/docs/레이어별_테이블구성.pdf)
- 📄 ERD / 데이터 모델 PDF 바로가기: [ERD 이미지 보기](./portfolio%201/docs/erd_diagram.PNG)

<br>
<br>

## 6. 분석 내용

**(1) 장기 상권 성장률 분석**

- 2023–2025년 분기 데이터를 기반으로 **상권별 성장률**을 계산합니다.
- 성장률 = (최신 매출 − 초기 매출) / 초기 매출


**(2) 최근 성장 상권 분석**

- 최근 **4개 분기 평균 성장률**을 산출하여 현재 **상승 중인 상권**을 탐색합니다.


**(3) 4분면 상권 분류**

| 유형 | 설명 |
|---|---|
| 🟢 방어 성장형 | 매출 + 최근 성장 모두 양호 |
| 🔵 회복 탄력형 | 과거 감소 후 최근 회복세 |
| 🟡 방어 침체형 | 안정적이나 완만한 감소 |
| 🔴 구조적 위험형 | 지속적 매출 감소 |


**(4) 매출 vs 유동인구 분석**

- **매출 증가와 유동인구 증가의 상관관계**를  
산점도로 시각화합니다.


**(5) 시간대 소비 패턴 분석**

- 시간대별 매출과 유동인구를 비교하여

      - 점심 상권
      - 저녁 상권
      - 야간 상권

   패턴을 확인합니다.


<br>
<br>


## 7. Streamlit 대시보드

🚀 **배포 주소**

https://seoul-commercial-insight.streamlit.app/

| 기능 | 설명 |
|---|---|
| 서울시 상권 지도 | 구 단위 매출 및 성장률 시각화 |
| 매출 TOP 10 | 최신 분기 기준 매출 상위 상권 순위 |
| Hot Area TOP 5 | 최근 성장률 상위 상권 순위 |
| 상세 분석 | 구 선택 시 시간대 · 성별 · 요일 · 유동인구 차트 제공 |


<br>
<br>


## 8. 주요 인사이트

일부 상권은 **매출 증가와 유동인구 증가가 동시에 나타나**  
**신흥 상권으로 성장할 가능성**을 보였습니다.

반면 **유동인구가 감소하는 지역에서는 구조적 침체 신호**가 함께 관찰되었습니다.

또한 **시간대 · 요일 패턴 분석을 통해 상권 유형별 소비 특성**을 구분할 수 있었습니다.

<br><br>




## 9. Repository 구조

```text
.
├─ notebooks/
│  ├─ 01_eda_livingpop.ipynb
│  ├─ 02_aggregation_quarter.ipynb
│  └─ 03_merge_sales_vacancy.ipynb
├─ sql/
│  ├─ 01_create_tables.sql
│  ├─ 02_create_indexes.sql
│  └─ 03_agg_livingpop_dong_quarter.sql
├─ docs/
│  ├─ erd.png
│  ├─ pipeline.png
│  └─ portfolio.pptx
├─ src/
│  ├─ extract.py
│  ├─ transform.py
│  └─ load_mysql.py
└─ data_sample/
   └─ sample.csv
```


<br>
<br>

## Contact
- GitHub: https://github.com/yubincho?tab=repositories
- Email: yubincho9@gmail.com

<br><br>

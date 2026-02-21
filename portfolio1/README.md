

<img width="180" height="190" alt="서울 지형 2" src="https://github.com/user-attachments/assets/13b58896-f5ed-419b-a178-ed05961222bf" />


---

# 서울시 상권 분석 (유동인구 × 매출 × 공실률)

## 유동인구 × 매출 × 공실률
### BigQuery 기반 ELT 데이터 파이프라인
<br>

서울시 **행정동 단위**로 유동인구 데이터를 **분기별로 집계**하고, 매출 및 공실률 데이터를 결합하여  
**상권 효율(유동인구 대비 매출)** 과 **상권 리스크(공실률 변화)** 를 분석하는  
**BigQuery 기반 ELT 데이터 파이프라인 프로젝트**입니다.

- **GCS → BigQuery → Analytics** 흐름의 ELT 아키텍처
- **Raw → Staging → Mart** 레이어 기반 데이터 모델링
- **행정동 × 분기** 단위 상권 변화 추적
  
> ⚠️ 머신러닝/딥러닝은 의도적으로 제외했습니다.  
> 본 프로젝트는 **데이터 웨어하우스 설계, 정합성 확보, 집계 로직 설계**에 집중하며,  
> **ELT 기반 데이터 모델링만으로도 충분히 설명 가능한 분석 인사이트 도출**을 목표로 합니다.


---
<br>

## 1. 프로젝트 목표

- 서울시 행정동 단위로 **유동인구 / 매출 / 공실률** 데이터를 통합 분석할 수 있는  
  **BigQuery 기반 분석 환경 구축**
- **Raw → Staging → Mart** 구조를 활용한 데이터 정제 및 집계 설계
- 분기별 상권 변화를 추적 가능한 **분석용 데이터마트(Mart)** 구축
- 향후 대시보드 및 고급 분석 확장을 고려한 **확장 가능한 데이터 구조 설계**

<br><br>

## 2. 사용 기술

- **Python**
  - 데이터 수집, 사전 검증, 보조 전처리
- **Airflow**
- **Google Cloud Storage (GCS)**  
  - 원천 데이터 적재 및 Raw 파일 보관
- **BigQuery**  
  - Raw / Staging / Mart 데이터셋 구성  
  - SQL 기반 데이터 변환 및 집계 (**ELT 방식**)
- **GitHub**: 프로젝트 버전 관리 및 문서화
- **(예정)** Streamlit 기반 대시보드

<br><br>

## 3. 데이터 파이프라인 구조 (ELT)

**Raw 데이터 → Staging 적재 → 행정동 매핑(Dimension) → 분기 집계(Mart) → 분석/시각화**


```text
┌────────────────────────────────────────────┐
│ Apache Airflow (Scheduling & Orchestration)│
│  - Extract DAG                              │
│  - Load to GCS                              │
│  - BigQuery Transform (SQL)                 │
└────────────────────────────────────────────┘
```



**레이어별 역할**

- Raw
   - GCS에 적재된 원천 데이터를 BigQuery로 그대로 로딩
   - 원본 보존 및 재처리 가능성 확보

- Staging
   - 컬럼 정리 및 타입 변환
   - 행정동 코드 정합성 확보
   - 결측치 및 중복 처리
   - ❗ 비즈니스 집계 로직은 포함하지 않음

- Mart
   - 행정동 × 분기 단위 집계
   - 분석 및 시각화에 직접 사용 가능한 지표 제공

<br><br>

## 4. 데이터 모델 
* 프로젝트 테이블 구성 (Raw → Staging → Analytics)
* 📄 ERD / 데이터 모델 PDF 바로가기: [데이터모델.pdf](https://github.com/yubincho/Portfolio_yubin/tree/main/portfolio%201/docs)
  <br>
- Dimension
  - dim_admin_dong : 행정동 기준 정보

- Staging
  - stg_livingpop_snapshot
  - stg_seoul_sales_quarter
  - stg_seoul_vacancy_rate

- Mart
  - agg_livingpop_dong_quarter
  - mart_sales_dong_quarter
  - mart_commercial_dong_quarter



<br><br>



## 5. 분석 아이디어 (예정)

### 5-1) 상권 효율 지표

분기 단위 행정동 기준으로 아래 지표를 정의하고, Top/Bottom 랭킹 및 유형 분석을 수행합니다.

1. **분기 유동인구 평균**  
   - `agg_livingpop_dong_quarter.유동인구_분기평균`

2. **유동인구 대비 매출 효율**  
   - `효율 = 매출 / 유동인구`

3. **공실률 변화율(분기 대비)**  
   - `변화율 = (이번 분기 공실률 - 이전 분기 공실률) / 이전 분기 공실률`

### 5-2) 상권 리스크 진단

- 공실률 상승 + 매출 하락 지역을 탐지하여 리스크 상권 후보를 도출
- 분기별 변화율을 기반으로 이상징후(급락/급등) 지역을 탐지

<br><br>

## 6. 대시보드 구성 (예정)

- 분기 선택 (예: 2023Q1 ~)
- 행정동 검색/필터
- 효율 Top/Bottom 랭킹
- 공실률 vs 효율 관계 시각화(Scatter)
- 분기별 트렌드(Line)

<br><br>

## 7. 프로젝트 진행 상황

- [x] 행정동 Dimension 테이블 구축 (`dim_admin_dong`)
- [x] GCS 기반 Raw 데이터 적재
- [x] BigQuery Raw / Staging 데이터셋 구성
- [x] 유동인구 Raw 적재 및 분기 집계 Mart 구축 (`agg_livingpop_dong_quarter`)
- [x] 매출/공실률 Staging 테이블 구축
- [ ] 통합 Mart (mart_commercial_dong_quarter) 완성
- [ ] 효율 지표 산출 및 인사이트 도출
- [ ] Streamlit 대시보드 구현 및 배포

<br><br>

## 8. Repository 구조

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

<br><br>

## 9. Roadmap
- BigQuery 파티셔닝 / 클러스터링 최적화
- Dataform 또는 dbt 도입을 통한 SQL 변환 관리
- Airflow 기반 스케줄링 자동화
- 분석 결과 대시보드 고도화

<br>
<br>

## Contact
- GitHub: https://github.com/yubincho?tab=repositories
- Email: yubincho9@gmail.com

<br><br>

---

# 조유빈(Yubin Cho) | Data Engineer Portfolio 🤗
안녕하세요. 데이터 엔지니어를 목표로 공부 중인 조유빈입니다.  
데이터를 단순히 분석하는 것을 넘어, **데이터 적재/정제/집계/모델링** 과정을 직접 구현하여  
재사용 가능한 데이터 구조를 만드는 프로젝트를 만들고 있습니다.

---

<img width="150" height="160" alt="서울도시" src="https://github.com/user-attachments/assets/ff773fee-2db8-46a2-aafd-56a3d5864bcc" />


# 서울시 상권 분석 (유동인구 × 매출 × 공실률)

서울시 **행정동 단위**로 유동인구 데이터를 **분기별로 집계**하고, 매출/공실률 데이터와 결합하여  
**상권 효율(유동인구 대비 매출)** 및 **상권 리스크(공실률 변화)** 를 분석하는 데이터 파이프라인 프로젝트입니다.

- **Raw → Staging → Mart** 구조로 데이터 모델링  
- **행정동 × 분기** 단위로 상권 변화 추적 및 효율 분석


> 머신러닝/딥러닝은 의도적으로 제외했습니다.  
> 먼저 **데이터 적재·정제·집계·모델링(Raw→Mart)** 기반을 탄탄히 구축하고,  
> EDA와 지표 분석만으로도 충분히 설명 가능한 인사이트 도출을 목표로 했습니다.


---

## 1. 프로젝트 목표

- 서울시 행정동 단위로 **유동인구 / 매출 / 공실률** 데이터를 통합 분석할 수 있는 기반 설계
- 분기별 상권 변화를 추적 가능한 **데이터마트(Aggregation Mart)** 구축
- 향후 대시보드를 통해 주요 지표 및 인사이트를 시각화하여 전달

---

## 2. 사용 기술

- **Python**: pandas, numpy (전처리 및 집계)
- **MySQL**: Staging / Dimension / Mart 테이블 설계 및 저장
- **GitHub**: 프로젝트 버전 관리 및 문서화
- **(예정) AWS EC2, RDS, Docker, Airflow**
- **(예정) 대시보드 구현 및 배포**

---

## 3. 데이터 파이프라인 구조

Raw 데이터 → Staging 적재 → 행정동 매핑(Dimension) → 분기 집계(Mart) → 분석/시각화

<img width="840" height="202" alt="image" src="https://github.com/user-attachments/assets/a53a5516-716e-457e-b4b5-081b03a0192c" />

- **유동인구 스냅샷**: 일별 원천 데이터를 적재 후 분기 단위로 집계
- **매출 데이터**: 분기 단위(행정동/업종 포함)로 Staging 적재
- **공실률 데이터**: 분석에 적합하도록 Long Format 형태로 적재

---

## 4. 데이터 모델 (현재 구축 완료 테이블 5개)

| 구분 | 테이블 | 설명 |
|---|---|---|
| Staging | `stg_metro_people_snapshot` | 서울시 유동인구 스냅샷 원천 데이터를 적재하는 Raw/Staging 테이블 |
| Dimension | `dim_admin_dong` | 행정동 코드 기준 표준 행정동 마스터 테이블 (시도/시군구/행정동 매핑) |
| Mart | `agg_livingpop_dong_quarter` | 유동인구 데이터를 행정동 × 분기 단위로 집계한 분석용 테이블 |
| Staging | `stg_seoul_sales_quarter` | 상권 매출 데이터를 분기 단위로 적재한 Staging 테이블 |
| Staging | `stg_seoul_vacancy_long` | 공실률 데이터를 Long Format 형태로 적재한 Staging 테이블 |

## ERD

<img width="935" height="3540" alt="ERD2" src="https://github.com/user-attachments/assets/bd53f3f2-e7d7-4f5e-a450-23c8a34dcd81" />

> ※ 공실률 데이터(`stg_seoul_vacancy_long`)는 지역 단위 컬럼(지역별1/2) 기반이므로,  
> 행정동 코드 매핑 테이블을 추가하여 결합하는 방향으로 확장 예정입니다.

---

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

---

## 6. 대시보드 구성 (예정)

- 분기 선택 (예: 2023Q1 ~)
- 행정동 검색/필터
- 효율 Top/Bottom 랭킹
- 공실률 vs 효율 관계 시각화(Scatter)
- 분기별 트렌드(Line)

---

## 7. 프로젝트 진행 상황

- [x] 행정동 Dimension 테이블 구축 (`dim_admin_dong`)
- [x] 유동인구 Raw 적재 및 분기 집계 Mart 구축 (`agg_livingpop_dong_quarter`)
- [x] 매출/공실률 Staging 테이블 구축
- [ ] 매출/공실률 Join 기준 확정 및 통합 분석 테이블 설계
- [ ] 효율 지표 산출 및 인사이트 도출
- [ ] Streamlit 대시보드 구현 및 배포

---

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

---

## Roadmap
- 데이터 품질(관측일수/커버리지) 지표를 활용한 검증 로직 강화
- RDS 마이그레이션 및 배포 환경 구성(EC2/Docker)
- Airflow 기반 스케줄링으로 ETL 자동화

---

## Contact
- GitHub: https://github.com/yubincho?tab=repositories
- Email: yubincho9@gmail.com

---

---

# 조유빈(Yubin Cho) | Data Engineer Portfolio 🤗
안녕하세요. 데이터 엔지니어를 목표로 공부 중인 조유빈입니다.  
데이터를 단순히 분석하는 것을 넘어, **데이터 적재/정제/집계/모델링** 과정을 직접 구현하여  
재사용 가능한 데이터 구조를 만드는 프로젝트를 만들고 있습니다.

---
<br>

## Portfolio 1 — 서울시 상권 분석 (유동인구 × 매출 × 공실률)

서울시 공공 데이터를 기반으로 **행정동 단위 상권 지표를 통합**하고,  
분기별로 상권의 **매출 효율(유동인구 대비 매출)** 및 **공실률** 관점에서 분석 가능한 데이터 마트를 구축했습니다.

- 데이터 파이프라인 구조: **Raw → Staging → Mart**
- 핵심 테이블: `stg_seoul_sales_quarter`, `mart_sales_dong_quarter`, `mart_commercial_dong_quarter`
- 목표: 상권 효율/변화 감지 및 비교 분석 기반 마련

➡️ 자세한 내용은 [`portfolio1/`](https://github.com/yubincho/Portfolio_yubin/tree/main/portfolio%201) 폴더에서 확인할 수 있습니다.

<br><br>

## ✅ Portfolio 2 — 서울시 상권 분석 (ML/DL 모델링 확장)

Portfolio 1에서 구축한 **행정동×분기 단위 통합 데이터 마트(유동인구 × 매출 × 공실률)**를 학습 데이터로 활용하여,  
머신러닝/딥러닝 기반으로 **상권 성과 예측 및 리스크 탐지 모델**까지 확장할 예정입니다.

### Modeling Goals
- **매출 효율 예측**
  - Target: `매출효율_금액 (총매출 / 유동인구)`
  - Models: **LightGBM, XGBoost, RandomForest**
  - Metrics: **RMSE, MAE, R²**

- **공실률 리스크 탐지**
  - Target: 공실률 증가 여부(분기 대비 상승) 분류
  - Models: **LightGBMClassifier, XGBoostClassifier, Logistic Regression**
  - Metrics: **F1-score, ROC-AUC, Precision/Recall**

- **상권 유형 군집화(세그먼트 분류)**
  - Models: **K-Means, Gaussian Mixture, HDBSCAN**
  - Metrics: **Silhouette Score, Davies–Bouldin Index**

- **분기별 트렌드/변화 예측(Time-series)**
  - Models: **LSTM / GRU, Temporal CNN**
  - Metrics: **MAE, RMSE, MAPE**

➡️ 프로젝트는 추후 `portfolio2/` 폴더에 정리할 예정입니다.



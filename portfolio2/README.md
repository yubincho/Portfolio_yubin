# Portfolio 2 — 서울시 상권 분석 (ML/DL 모델링 확장)

Portfolio 1에서 구축한 **행정동×분기 단위 통합 데이터 마트(유동인구 × 매출 × 공실률)**를 학습 데이터로 활용하여,  
머신러닝/딥러닝 기반으로 **상권 성과 예측 및 리스크 탐지 모델**까지 확장할 예정입니다.

## Modeling Goals

### 1) 매출 효율 예측
- Target: `매출효율_금액 (총매출 / 유동인구)`
- Models: **LightGBM, XGBoost, RandomForest**
- Metrics: **RMSE, MAE, R²**

### 2) 공실률 리스크 탐지
- Target: 공실률 증가 여부(분기 대비 상승) 분류
- Models: **LightGBMClassifier, XGBoostClassifier, Logistic Regression**
- Metrics: **F1-score, ROC-AUC, Precision/Recall**

### 3) 상권 유형 군집화(세그먼트 분류)
- Models: **K-Means, Gaussian Mixture, HDBSCAN**
- Metrics: **Silhouette Score, Davies–Bouldin Index**

### 4) 분기별 트렌드/변화 예측(Time-series)
- Models: **LSTM / GRU, Temporal CNN**
- Metrics: **MAE, RMSE, MAPE**

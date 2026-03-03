{{ config(materialized='table', schema='mart') }}

WITH base AS (
  SELECT
    admin_dong_code,
    EXTRACT(DAYOFWEEK FROM base_date) AS weekday_num,  -- 1=일,7=토 (실제 데이터는 2~6만 존재)
    time_slot,
    total_population
  FROM `smart-paratext-486618-v8.stg.stg_living_population`
)

SELECT
  admin_dong_code,
  weekday_num,
  time_slot,
  AVG(total_population) AS avg_population
FROM base
GROUP BY 1,2,3
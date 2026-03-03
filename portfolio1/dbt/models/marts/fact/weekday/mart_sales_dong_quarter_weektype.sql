{{ config(materialized='table', schema='mart') }}

WITH base AS (
  SELECT
    year,
    quarter,
    admin_dong_code,
    sales_amount_weekday,
    sales_amount_weekend
  FROM `smart-paratext-486618-v8.stg.stg_seoul_sales`
)

SELECT
  year,
  quarter,
  admin_dong_code,
  'weekday' AS week_type,
  SUM(sales_amount_weekday) AS total_sales
FROM base
GROUP BY 1,2,3

UNION ALL

SELECT
  year,
  quarter,
  admin_dong_code,
  'weekend' AS week_type,
  SUM(sales_amount_weekend) AS total_sales
FROM base
GROUP BY 1,2,3
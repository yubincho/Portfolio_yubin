{{ config(materialized='table', schema='mart') }}

WITH pop_weekday AS (
  SELECT
    EXTRACT(YEAR FROM base_date) AS year,
    EXTRACT(QUARTER FROM base_date) AS quarter,
    admin_dong_code,
    AVG(total_population) AS avg_weekday_population
  FROM `smart-paratext-486618-v8.stg.stg_living_population`
  GROUP BY 1,2,3
),

sales_weekday AS (
  SELECT
    year,
    quarter,
    admin_dong_code,
    SUM(sales_amount_weekday) AS weekday_sales
  FROM `smart-paratext-486618-v8.stg.stg_seoul_sales`
  GROUP BY 1,2,3
)

SELECT
  s.year,
  s.quarter,
  s.admin_dong_code,
  p.avg_weekday_population,
  s.weekday_sales,
  SAFE_DIVIDE(s.weekday_sales, p.avg_weekday_population) AS sales_per_person
FROM sales_weekday s
LEFT JOIN pop_weekday p
  ON s.year = p.year
 AND s.quarter = p.quarter
 AND s.admin_dong_code = p.admin_dong_code
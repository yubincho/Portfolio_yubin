{{ config(materialized='table', schema='mart') }}

WITH base AS (
  SELECT
    admin_dong_code,
    EXTRACT(ISOYEAR FROM base_date) AS iso_year,
    EXTRACT(ISOWEEK FROM base_date) AS iso_week,
    time_slot,
    total_population
  FROM `smart-paratext-486618-v8.stg.stg_living_population`
)

SELECT
  admin_dong_code,
  iso_year,
  iso_week,
  time_slot,
  AVG(total_population) AS avg_population
FROM base
GROUP BY 1,2,3,4
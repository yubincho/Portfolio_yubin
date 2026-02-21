{{ config(
    materialized='table',
    schema='mart',
    cluster_by=["admin_dong_code", "year", "quarter"]
) }}

select
  admin_dong_code,
  year,
  quarter,
  avg(avg_daily_population) as avg_quarter_population
from {{ ref('mart_livingpop_dong_day') }}
group by
  admin_dong_code,
  year,
  quarter
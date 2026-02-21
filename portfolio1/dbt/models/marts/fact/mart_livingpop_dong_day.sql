{{ config(
    materialized='table',
    schema='mart',
    partition_by={"field": "base_date", "data_type": "date"},
    cluster_by=["admin_dong_code"]
) }}

select
  admin_dong_code,
  base_date,
  year,
  quarter,
  avg(total_population) as avg_daily_population
from {{ ref('stg_living_population') }}
group by
  admin_dong_code,
  base_date,
  year,
  quarter
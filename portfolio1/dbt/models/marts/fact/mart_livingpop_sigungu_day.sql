{{ config(
    materialized='table',
    schema='mart',
    partition_by={"field": "base_date", "data_type": "date"},
    cluster_by=["sigungu_name"]
) }}

select
  d.sigungu_name,
  f.base_date,
  f.year,
  f.quarter,
  avg(f.avg_daily_population) as avg_daily_population
from {{ ref('mart_livingpop_dong_day') }} f
join {{ ref('dim_admin_dong') }} d
  on f.admin_dong_code = d.admin_dong_code
group by
  d.sigungu_name,
  f.base_date,
  f.year,
  f.quarter
{{ config(materialized='table', schema='mart') }}

select
  l.year,
  l.quarter,
  d.sigungu_name,
  l.bucket_id,
  l.time_bucket,
  sum(l.avg_population) as avg_population_sum
from {{ ref('mart_livingpop_dong_quarter_time') }} l
join {{ ref('dim_admin_dong') }} d
  on l.admin_dong_code = d.admin_dong_code
group by 1,2,3,4,5
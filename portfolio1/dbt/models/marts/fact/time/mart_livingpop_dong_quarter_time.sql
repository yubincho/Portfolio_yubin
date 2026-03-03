{{ config(materialized='table', schema='mart') }}

select
  l.year,
  l.quarter,
  l.admin_dong_code,
  b.bucket_id,
  b.label as time_bucket,
  avg(l.total_population) as avg_population
from {{ ref('stg_living_population') }} l
join {{ ref('dim_time_bucket') }} b
  on l.time_slot >= b.start_hour
 and l.time_slot <  b.end_hour
group by 1,2,3,4,5
{{ config(materialized='table', schema='mart') }}

select
  s.year,
  s.quarter,
  s.admin_dong_code,
  s.bucket_id,
  s.time_bucket,
  s.sales_amount,
  l.avg_population,
  safe_divide(s.sales_amount, l.avg_population) as sales_per_person
from {{ ref('mart_sales_dong_quarter_time') }} s
left join {{ ref('mart_livingpop_dong_quarter_time') }} l
  on s.year = l.year
 and s.quarter = l.quarter
 and s.admin_dong_code = l.admin_dong_code
 and s.bucket_id = l.bucket_id
{{ config(materialized='table', schema='mart') }}

select
  s.year,
  s.quarter,
  s.sigungu_name,
  s.bucket_id,
  s.time_bucket,
  s.sales_amount,
  l.avg_population_sum,
  safe_divide(s.sales_amount, l.avg_population_sum) as sales_per_person
from {{ ref('mart_sales_sigungu_quarter_time') }} s
left join {{ ref('mart_livingpop_sigungu_quarter_time') }} l
  on s.year = l.year
 and s.quarter = l.quarter
 and s.sigungu_name = l.sigungu_name
 and s.bucket_id = l.bucket_id
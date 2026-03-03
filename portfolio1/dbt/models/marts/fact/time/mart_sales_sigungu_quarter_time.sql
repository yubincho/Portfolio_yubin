{{ config(materialized='table', schema='mart') }}

select
  s.year,
  s.quarter,
  d.sigungu_name,
  s.bucket_id,
  s.time_bucket,
  sum(s.sales_amount) as sales_amount
from {{ ref('mart_sales_dong_quarter_time') }} s
join {{ ref('dim_admin_dong') }} d
  on s.admin_dong_code = d.admin_dong_code
group by 1,2,3,4,5
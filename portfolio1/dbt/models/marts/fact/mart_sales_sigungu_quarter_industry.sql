{{ config(materialized='table',schema='mart') }}

select
  d.sigungu_name,
  f.year,
  f.quarter,
  f.service_industry_code,
  f.service_industry_name,
  sum(f.sales_amount)as sales_amount,
  sum(f.sales_count)as sales_count
from {{ref('mart_sales_dong_quarter_industry') }} f
join {{ref('dim_admin_dong') }} d
on f.admin_dong_code= d.admin_dong_code
group by
  d.sigungu_name,
  f.year,
  f.quarter,
  f.service_industry_code,
  f.service_industry_name
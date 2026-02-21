{{ config(materialized='table',schema='mart') }}

select
year,
  quarter,
  service_industry_code,
  service_industry_name,
  sum(sales_amount)as sales_amount,
  sum(sales_count)as sales_count
from {{ref('mart_sales_dong_quarter_industry') }}
group by
  year,
  quarter,
  service_industry_code,
  service_industry_name
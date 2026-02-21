{{ config(materialized='table', schema='mart') }}

select
  admin_dong_code,
  year,
  quarter,
  sum(sales_amount) as sales_amount,
  sum(sales_count)  as sales_count
from {{ ref('mart_sales_dong_quarter_industry') }}
group by
  admin_dong_code,
  year,
  quarter
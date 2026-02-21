{{ config(materialized='table',schema='mart') }}

select
year,
  quarter,
  sum(sales_amount)as sales_amount,
  sum(sales_count)as sales_count
from {{ref('mart_sales_dong_quarter') }}
group by
  year,
  quarter
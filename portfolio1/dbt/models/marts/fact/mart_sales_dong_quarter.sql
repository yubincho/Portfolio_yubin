{{ config(materialized='table', schema='mart') }}

select
    admin_dong_code,
    year,
    quarter,

    sum(sales_amount_month) as total_sales_amount,
    sum(sales_cnt_month)    as total_sales_count

from {{ ref('stg_seoul_sales') }}

group by
    admin_dong_code,
    year,
    quarter
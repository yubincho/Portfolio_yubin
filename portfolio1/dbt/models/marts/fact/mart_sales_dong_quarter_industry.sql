{{ config(
    materialized='table',
    schema='mart'
) }}

select
    s.admin_dong_code,
    s.year,
    s.quarter,
    s.service_industry_code,
    s.service_industry_name,

    sum(s.sales_amount_month) as sales_amount,
    sum(s.sales_cnt_month) as sales_count

from {{ ref('stg_seoul_sales') }} s

group by
    s.admin_dong_code,
    s.year,
    s.quarter,
    s.service_industry_code,
    s.service_industry_name
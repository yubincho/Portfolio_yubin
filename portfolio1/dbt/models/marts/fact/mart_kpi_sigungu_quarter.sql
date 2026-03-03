{{ config(
    materialized='table',
    schema='mart'
) }}

with base as (

    select
        d.sigungu_name,
        s.year,
        s.quarter,

        sum(s.sales_amount) as total_sales_amount,
        sum(s.sales_count) as total_sales_count,
        sum(l.avg_quarter_population) as total_avg_quarter_population

    from {{ ref('mart_sales_dong_quarter') }} s
    join {{ ref('mart_livingpop_dong_quarter') }} l
      on s.year = l.year
     and s.quarter = l.quarter
     and s.admin_dong_code = l.admin_dong_code

    join {{ ref('dim_admin_dong') }} d
      on s.admin_dong_code = d.admin_dong_code

    group by
        d.sigungu_name,
        s.year,
        s.quarter
)

select
    year,
    quarter,
    sigungu_name,
    total_sales_amount,
    total_sales_count,
    total_avg_quarter_population,
    safe_divide(total_sales_amount, total_avg_quarter_population) as sales_per_capita
from base
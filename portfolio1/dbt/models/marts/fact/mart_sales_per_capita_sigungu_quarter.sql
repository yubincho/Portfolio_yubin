{{ config(
    materialized='table',
    schema='mart',
    partition_by={"field": "quarter_start_date", "data_type": "date"},
    cluster_by=["sigungu_name"]
) }}

select
  s.sigungu_name,
  s.year,
  s.quarter,
  DATE(s.year, (s.quarter - 1) * 3 + 1, 1) as quarter_start_date,
  s.sales_amount,
  s.sales_count,
  p.avg_quarter_population,
  safe_divide(s.sales_amount, p.avg_quarter_population) as sales_per_capita
from {{ ref('mart_sales_sigungu_quarter') }} s
left join {{ ref('mart_livingpop_sigungu_quarter') }} p
  on s.sigungu_name = p.sigungu_name
 and s.year = p.year
 and s.quarter = p.quarter
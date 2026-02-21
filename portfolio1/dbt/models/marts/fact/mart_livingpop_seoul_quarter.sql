{{ config(
    materialized='table',
    schema='mart',
    partition_by={"field": "quarter_start_date", "data_type": "date"}
) }}

select
  year,
  quarter,
  DATE(year, (quarter - 1) * 3 + 1, 1) as quarter_start_date,
  avg(avg_quarter_population) as avg_quarter_population
from {{ ref('mart_livingpop_sigungu_quarter') }}
group by
  year,
  quarter,
  quarter_start_date
{{ config(
    materialized='table',
    schema='mart',
    partition_by={"field": "quarter_start_date", "data_type": "date"},
    cluster_by=["sigungu_name"]
) }}

with base as (
  select
    sigungu_name,
    year,
    quarter,
    DATE(year, (quarter - 1) * 3 + 1, 1) as quarter_start_date,
    avg(avg_daily_population) as avg_quarter_population
  from {{ ref('mart_livingpop_sigungu_day') }}
  group by
    sigungu_name,
    year,
    quarter
)

select *
from base
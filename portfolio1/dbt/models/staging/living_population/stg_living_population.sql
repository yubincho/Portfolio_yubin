{{ config(materialized='view', schema='stg') }}

with unioned as (

    select
      `기준일ID`,
      `행정동코드`,
      `시간대구분`,
      `총생활인구수`
    from {{ source('raw','living_population_raw_2023') }}

    union all

    select
      `기준일ID`,
      `행정동코드`,
      `시간대구분`,
      `총생활인구수`
    from {{ source('raw','living_population_raw_2024') }}

    union all

    select
      `기준일ID`,
      `행정동코드`,
      `시간대구분`,
      `총생활인구수`
    from {{ source('raw','living_population_raw_2025') }}

),

cleaned as (

    select
        cast(`기준일ID` as string) as base_date_str,
        parse_date('%Y%m%d', cast(`기준일ID` as string)) as base_date,

        extract(year from parse_date('%Y%m%d', cast(`기준일ID` as string))) as year,
        extract(quarter from parse_date('%Y%m%d', cast(`기준일ID` as string))) as quarter,

        cast(`행정동코드` as string) as admin_dong_code,   -- 여기 컬럼이 8자리 코드여야 함

        cast(`시간대구분` as int64) as time_slot,
        cast(`총생활인구수` as int64) as total_population

    from unioned
)

select *
from cleaned
where base_date is not null
  and total_population is not null
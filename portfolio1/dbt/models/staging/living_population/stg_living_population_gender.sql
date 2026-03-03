{{ config(materialized='view', schema='stg') }}

with union_raw as (
  select * from {{ source('raw', 'living_population_raw_2023') }}
  union all
  select * from {{ source('raw', 'living_population_raw_2024') }}
  union all
  select * from {{ source('raw', 'living_population_raw_2025') }}
),

typed as (
  select
    parse_date('%Y%m%d', cast(`기준일ID` as string)) as base_date,
    extract(year from parse_date('%Y%m%d', cast(`기준일ID` as string))) as year,
    extract(quarter from parse_date('%Y%m%d', cast(`기준일ID` as string))) as quarter,

    cast(`시간대구분` as int64) as time_slot,
    lpad(cast(`행정동코드` as string), 10, '0') as admin_dong_code,

    -- helper inline: 숫자/소수만 남기고 캐스팅, 실패시 0
    (
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자10세부터14세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자15세부터19세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자20세부터24세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자25세부터29세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자30세부터34세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자35세부터39세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자40세부터44세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자45세부터49세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자50세부터54세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자55세부터59세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자60세부터64세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자65세부터69세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자70세부터74세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`남자75세부터79세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0)
    ) as male_population,

    (
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자10세부터14세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자15세부터19세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자20세부터24세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자25세부터29세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자30세부터34세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자35세부터39세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자40세부터44세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자45세부터49세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자50세부터54세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자55세부터59세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자60세부터64세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자65세부터69세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자70세부터74세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0) +
      coalesce(safe_cast(nullif(regexp_extract(cast(`여자75세부터79세생활인구수` as string), r'^\d+(\.\d+)?$'), '') as float64), 0)
    ) as female_population

  from union_raw
)

select
  base_date,
  year,
  quarter,
  time_slot,
  admin_dong_code,
  male_population,
  female_population,
  male_population + female_population as total_population
from typed
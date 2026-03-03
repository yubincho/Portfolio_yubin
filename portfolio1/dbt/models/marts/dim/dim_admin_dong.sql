{{ config(materialized='table', schema='mart') }}

with base as (
  select distinct
    cast(`행정동코드` as string) as admin_dong_code,
    cast(`시도명` as string)      as sido_name,
    cast(`시군구명` as string)    as sigungu_name,
    cast(`읍면동명` as string)    as admin_dong_name
  from {{ source('raw', 'admin_dong_raw') }}
  where `행정동코드` is not null
    and `시도명` = '서울특별시'
),

patch as (
  select
    '11680740' as admin_dong_code,
    '서울특별시' as sido_name,
    '강남구' as sigungu_name,
    cast(null as string) as admin_dong_name
  union all
  select
    '11740520' as admin_dong_code,
    '서울특별시' as sido_name,
    '강동구' as sigungu_name,
    cast(null as string) as admin_dong_name
),

unioned as (
  select * from base
  union all
  select * from patch
)

select
  admin_dong_code,
  any_value(sido_name) as sido_name,
  any_value(sigungu_name) as sigungu_name,
  any_value(admin_dong_name) as admin_dong_name
from unioned
group by 1
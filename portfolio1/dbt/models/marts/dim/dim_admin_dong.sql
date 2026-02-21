{{ config(materialized='table', schema='mart') }}

select distinct
    cast(`행정동코드` as string)      as admin_dong_code,
    `시도명`                        as sido_name,
    `시군구명`                      as sigungu_name,
    `읍면동명`                      as dong_name
from {{ source('raw', 'admin_dong_raw') }}
where `행정동코드` is not null

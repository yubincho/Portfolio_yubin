{{ config(materialized='view', schema='stg') }}

with src as (
  select
    -- keys
    cast(`기준_년분기_코드` as int64) as year_quarter_code,         -- e.g. 20231
    cast(`행정동_코드` as string) as admin_dong_code,  -- 8자리
    `행정동_코드_명` as admin_dong_name,
    `서비스_업종_코드` as service_industry_code,
    `서비스_업종_코드_명` as service_industry_name,

    -- sales amount
    `당월_매출_금액` as sales_amount_month,
    `주중_매출_금액` as sales_amount_weekday,
    `주말_매출_금액` as sales_amount_weekend,
    `월요일_매출_금액` as sales_amount_mon,
    `화요일_매출_금액` as sales_amount_tue,
    `수요일_매출_금액` as sales_amount_wed,
    `목요일_매출_금액` as sales_amount_thu,
    `금요일_매출_금액` as sales_amount_fri,
    `토요일_매출_금액` as sales_amount_sat,
    `일요일_매출_금액` as sales_amount_sun,
    `시간대_00_06_매출_금액` as sales_amount_00_06,
    `시간대_06_11_매출_금액` as sales_amount_06_11,
    `시간대_11_14_매출_금액` as sales_amount_11_14,
    `시간대_14_17_매출_금액` as sales_amount_14_17,
    `시간대_17_21_매출_금액` as sales_amount_17_21,
    `시간대_21_24_매출_금액` as sales_amount_21_24,
    `남성_매출_금액` as sales_amount_male,
    `여성_매출_금액` as sales_amount_female,
    `연령대_10_매출_금액` as sales_amount_age_10,
    `연령대_20_매출_금액` as sales_amount_age_20,
    `연령대_30_매출_금액` as sales_amount_age_30,
    `연령대_40_매출_금액` as sales_amount_age_40,
    `연령대_50_매출_금액` as sales_amount_age_50,
    `연령대_60_이상_매출_금액` as sales_amount_age_60_plus,

    -- sales count
    `당월_매출_건수` as sales_cnt_month,
    `주중_매출_건수` as sales_cnt_weekday,
    `주말_매출_건수` as sales_cnt_weekend,
    `월요일_매출_건수` as sales_cnt_mon,
    `화요일_매출_건수` as sales_cnt_tue,
    `수요일_매출_건수` as sales_cnt_wed,
    `목요일_매출_건수` as sales_cnt_thu,
    `금요일_매출_건수` as sales_cnt_fri,
    `토요일_매출_건수` as sales_cnt_sat,
    `일요일_매출_건수` as sales_cnt_sun,
    `시간대_건수_06_매출_건수` as sales_cnt_06,
    `시간대_건수_11_매출_건수` as sales_cnt_11,
    `시간대_건수_14_매출_건수` as sales_cnt_14,
    `시간대_건수_17_매출_건수` as sales_cnt_17,
    `시간대_건수_21_매출_건수` as sales_cnt_21,
    `시간대_건수_24_매출_건수` as sales_cnt_24,
    `남성_매출_건수` as sales_cnt_male,
    `여성_매출_건수` as sales_cnt_female,
    `연령대_10_매출_건수` as sales_cnt_age_10,
    `연령대_20_매출_건수` as sales_cnt_age_20,
    `연령대_30_매출_건수` as sales_cnt_age_30,
    `연령대_40_매출_건수` as sales_cnt_age_40,
    `연령대_50_매출_건수` as sales_cnt_age_50,
    `연령대_60_이상_매출_건수` as sales_cnt_age_60_plus

  from {{ source('raw', 'seoul_sales_raw') }}
)

select
  *,
  -- year_quarter_code = 20231 형태를 가정
  cast(floor(year_quarter_code / 10) as int64) as year,
  cast(mod(year_quarter_code, 10) as int64) as quarter
from src
where admin_dong_code is not null
  and year_quarter_code is not null
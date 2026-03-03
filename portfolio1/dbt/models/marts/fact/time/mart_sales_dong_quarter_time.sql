{{ config(materialized='table', schema='mart') }}

with base as (
  select
    -- 20253 같은 값이면 year/quarter가 없을 수 있으니 안전하게 파싱 (있으면 그냥 year, quarter 쓰면 됨)
    cast(floor(cast(year_quarter_code as int64) / 10) as int64) as year,
    cast(mod(cast(year_quarter_code as int64), 10) as int64) as quarter,
    admin_dong_code,

    cast(sales_amount_00_06 as int64) as sales_amount_00_06,
    cast(sales_amount_06_11 as int64) as sales_amount_06_11,
    cast(sales_amount_11_14 as int64) as sales_amount_11_14,
    cast(sales_amount_14_17 as int64) as sales_amount_14_17,
    cast(sales_amount_17_21 as int64) as sales_amount_17_21,
    cast(sales_amount_21_24 as int64) as sales_amount_21_24
  from {{ ref('stg_seoul_sales') }}
),

unpvt as (
  select
    year,
    quarter,
    admin_dong_code,
    replace(time_col, 'sales_amount_', '') as time_label, -- '00_06'...
    sales_amount
  from base
  unpivot (
    sales_amount for time_col in (
      sales_amount_00_06,
      sales_amount_06_11,
      sales_amount_11_14,
      sales_amount_14_17,
      sales_amount_17_21,
      sales_amount_21_24
    )
  )
)

select
  u.year,
  u.quarter,
  u.admin_dong_code,
  b.bucket_id,
  b.label as time_bucket,
  sum(u.sales_amount) as sales_amount
from unpvt u
join {{ ref('dim_time_bucket') }} b
  on u.time_label = b.label
group by 1,2,3,4,5
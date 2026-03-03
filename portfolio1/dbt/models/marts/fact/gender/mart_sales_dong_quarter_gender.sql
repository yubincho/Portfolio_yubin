{{ config(materialized='table', schema='mart') }}

with base as (
  select
    year,
    quarter,
    admin_dong_code,
    cast(sales_amount_male as int64)   as sales_amount_male,
    cast(sales_amount_female as int64) as sales_amount_female
  from {{ ref('stg_seoul_sales') }}
),

unpvt as (
  select
    year,
    quarter,
    admin_dong_code,
    gender_col,
    sales_amount
  from base
  unpivot (
    sales_amount for gender_col in (
      sales_amount_male,
      sales_amount_female
    )
  )
)

select
  year,
  quarter,
  admin_dong_code,
  case
    when gender_col = 'sales_amount_male' then 'M'
    when gender_col = 'sales_amount_female' then 'F'
  end as gender,
  sum(sales_amount) as sales_amount
from unpvt
group by 1,2,3,4
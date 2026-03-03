{{ config(materialized='table', schema='mart') }}

with sales as (

  select
    year,
    quarter,
    admin_dong_code,
    gender,
    sales_amount
  from {{ ref('mart_sales_dong_quarter_gender') }}

),

living as (

  select
    year,
    quarter,
    admin_dong_code,
    gender,
    avg_population
  from {{ ref('mart_livingpop_dong_quarter_gender') }}

),

joined as (

  select
    s.year,
    s.quarter,
    s.admin_dong_code,
    s.gender,
    s.sales_amount,
    l.avg_population
  from sales s
  left join living l
    on s.year = l.year
   and s.quarter = l.quarter
   and s.admin_dong_code = l.admin_dong_code
   and s.gender = l.gender

),

final as (

  select
    *,
    safe_divide(
      sales_amount,
      sum(sales_amount) over (
        partition by year, quarter, admin_dong_code
      )
    ) as sales_share,

    safe_divide(
      avg_population,
      sum(avg_population) over (
        partition by year, quarter, admin_dong_code
      )
    ) as population_share

  from joined

)

select
  *,
  safe_divide(sales_share, population_share) as conversion_index
from final
where avg_population is not null   -- 유동인구 없는 행 제거
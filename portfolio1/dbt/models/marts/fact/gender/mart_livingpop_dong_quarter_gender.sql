{{ config(materialized='table', schema='mart') }}

with base as (
  select
    year,
    quarter,
    admin_dong_code,
    male_population,
    female_population
  from {{ ref('stg_living_population_gender') }}
),

unpvt as (
  select
    year,
    quarter,
    admin_dong_code,
    gender_col,
    population
  from base
  unpivot (
    population for gender_col in (
      male_population,
      female_population
    )
  )
)

select
  year,
  quarter,
  admin_dong_code,
  case
    when gender_col = 'male_population' then 'M'
    when gender_col = 'female_population' then 'F'
  end as gender,
  avg(population) as avg_population
from unpvt
group by 1,2,3,4
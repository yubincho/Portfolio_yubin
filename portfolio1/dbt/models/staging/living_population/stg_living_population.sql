{{ config(materialized='view') }}

select * from {{ source('raw', 'living_population_raw_2023') }}
union all
select * from {{ source('raw', 'living_population_raw_2024') }}
union all
select * from {{ source('raw', 'living_population_raw_2025') }}
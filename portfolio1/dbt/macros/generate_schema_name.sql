{% macro generate_schema_name(custom_schema_name, node) -%}
  {# 
    BigQuery에서 dataset(schema)이 profiles dataset과 결합되어
    stg_mart / dbt_mart 처럼 생성되는 것을 방지.
    custom_schema_name이 있으면 그걸 그대로 쓰고,
    없으면 profiles의 target.schema(dataset)을 사용.
  #}

  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name }}
  {%- endif -%}

{%- endmacro %}
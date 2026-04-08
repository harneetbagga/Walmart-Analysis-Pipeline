{{ config(materialized='table') }}

SELECT DISTINCT
    DATE_ID,
    FACT_DATE AS STORE_DATE,
    IS_HOLIDAY,
    CURRENT_TIMESTAMP() AS INSERT_DATE,
    CURRENT_TIMESTAMP() AS UPDATE_DATE

FROM {{ ref('int_walmart') }}
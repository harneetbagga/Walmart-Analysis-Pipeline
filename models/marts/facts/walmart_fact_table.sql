SELECT
    STORE_ID,
    DEPARTMENT_ID,
    DATE_ID,

    STORE_SIZE,
    STORE_WEEKLY_SALES,
    FUEL_PRICE,
    TEMPERATURE,
    UNEMPLOYMENT,
    CPI,

    MARKDOWN1,
    MARKDOWN2,
    MARKDOWN3,
    MARKDOWN4,
    MARKDOWN5,

    dbt_valid_from AS VRSN_START_DATE,
    dbt_valid_to AS VRSN_END_DATE,
    INSERT_DATE,
    UPDATE_DATE

FROM {{ref('walmart_fact_snapshot')}}
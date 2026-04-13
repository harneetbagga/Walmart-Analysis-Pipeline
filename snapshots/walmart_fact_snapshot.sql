{% snapshot walmart_fact_snapshot %}

{{
    config
        (
            target_schema='SNAPSHOTS',
            unique_key='UNIQUE_KEY',
            strategy='timestamp',
            updated_at='RECORD_LAST_UPDATED_TS'
        )
}}

SELECT
    UNIQUE_KEY,
    STORE_ID,
    DEPARTMENT_ID,
    DATE_ID,
    FACT_DATE,
    STORE_TYPE,
    STORE_SIZE,
    WEEKLY_SALES AS STORE_WEEKLY_SALES,
    FUEL_PRICE,
    TEMPERATURE,
    UNEMPLOYMENT,
    CPI,
    MARKDOWN1,
    MARKDOWN2,
    MARKDOWN3,
    MARKDOWN4,
    MARKDOWN5,
    IS_HOLIDAY,

    FACT_INSERT_DTS AS INSERT_DATE,
    FACT_UPDATE_DTS AS UPDATE_DATE,

    RECORD_LAST_UPDATED_TS

FROM {{ ref('int_walmart') }}

{% endsnapshot %}
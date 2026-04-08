{% snapshot walmart_fact_snapshot %}

{{
    config
        (
            target_schema='SNAPSHOTS',
            unique_key='STORE_ID || DEPARTMENT_ID || DATE_ID',
            strategy='timestamp',
            updated_at='RECORD_LAST_UPDATED_TS'
        )
}}

SELECT
    STORE_ID,
    DEPARTMENT_ID,
    DATE_ID,

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

    FACT_INSERT_DTS AS INSERT_DATE,
    FACT_UPDATE_DTS AS UPDATE_DATE,

    GREATEST(
    FACT_UPDATE_DTS,
    DEPT_UPDATE_DTS,
    STORE_UPDATE_DTS
    ) AS RECORD_LAST_UPDATED_TS

FROM {{ ref('int_walmart') }}

{% endsnapshot %}
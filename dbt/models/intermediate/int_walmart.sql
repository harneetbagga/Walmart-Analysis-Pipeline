{{ config(
    schema='INTEGRATION',
    materialized='view'
) }}

WITH base AS (

    SELECT
        F.STORE_ID,
        D.DEPARTMENT_ID,
        TO_NUMBER(TO_CHAR(F.FACT_DATE, 'YYYYMMDD')) AS DATE_ID,
        F.STORE_ID || '-' || D.DEPARTMENT_ID || '-' || DATE_ID AS UNIQUE_KEY,
        F.FACT_DATE,
        D.WEEKLY_SALES,
        S.STORE_TYPE,
        S.STORE_SIZE,

        F.TEMPERATURE,
        F.FUEL_PRICE,
        F.CPI,
        COALESCE(F.UNEMPLOYMENT, 0) AS UNEMPLOYMENT,

        F.MARKDOWN1,
        F.MARKDOWN2,
        F.MARKDOWN3,
        F.MARKDOWN4,
        F.MARKDOWN5,

        F.IS_HOLIDAY,

        F.INSERT_DTS AS FACT_INSERT_DTS,
        F.UPDATE_DTS AS FACT_UPDATE_DTS,

        D.INSERT_DTS AS DEPT_INSERT_DTS,
        D.UPDATE_DTS AS DEPT_UPDATE_DTS,

        S.INSERT_DTS AS STORE_INSERT_DTS,
        S.UPDATE_DTS AS STORE_UPDATE_DTS,

        -- Get the last updated timestamp across all source tables
    COALESCE(
        GREATEST(
            F.UPDATE_DTS,
            D.UPDATE_DTS,
            S.UPDATE_DTS
        ),
        CURRENT_TIMESTAMP()
) AS RECORD_LAST_UPDATED_TS

    FROM {{ ref('stg_walmart_fact') }} F

    LEFT JOIN {{ ref('stg_walmart_department') }} D
        ON F.STORE_ID = D.STORE_ID

    LEFT JOIN {{ ref('stg_walmart_store') }} S
        ON F.STORE_ID = S.STORE_ID

),

deduped AS (

    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY STORE_ID, DEPARTMENT_ID, DATE_ID
                   ORDER BY RECORD_LAST_UPDATED_TS DESC
               ) AS rn
        FROM base
    ) sub
    WHERE rn = 1

)

SELECT *
FROM deduped
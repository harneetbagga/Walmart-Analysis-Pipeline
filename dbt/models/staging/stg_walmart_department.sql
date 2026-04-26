WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY STORE_ID,DEPARTMENT_ID,DEPARTMENT_DATE
               ORDER BY UPDATE_DTS DESC
           ) AS rn
    FROM {{ source('bronze', 'WALLMART_DEPARTMENT') }}
)

SELECT
    -- clean + rename columns
    STORE_ID,
    DEPARTMENT_ID,
    CAST(DEPARTMENT_DATE AS DATE) AS DATE,
    WEEKLY_SALES,
    IS_HOLIDAY,
    INSERT_DTS,
    UPDATE_DTS,
    -- metadata columns from Snowpipe
    SOURCE_FILE_NAME,
    SOURCE_FILE_ROW_NUMBER

FROM ranked
WHERE rn=1
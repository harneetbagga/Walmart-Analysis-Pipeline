WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY STORE_ID
               ORDER BY UPDATE_DTS DESC
           ) AS rn
    FROM {{ source('bronze', 'WALLMART_STORES') }}
)

SELECT
    -- clean + rename columns
    STORE_ID,
    STORE_TYPE,
    STORE_SIZE,
    INSERT_DTS,
    UPDATE_DTS,
    -- metadata columns from Snowpipe
    SOURCE_FILE_NAME,
    SOURCE_FILE_ROW_NUMBER
    
    -- ensure correct data types
    -- CAST(sale_date AS DATE) AS sale_date,

FROM ranked
WHERE rn=1
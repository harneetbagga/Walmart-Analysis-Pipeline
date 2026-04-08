{{ config(materialized='table') }}

WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY STORE_ID, DEPARTMENT_ID
               ORDER BY DEPT_UPDATE_DTS DESC
           ) AS rn
    FROM {{ ref('int_walmart') }}
)

SELECT
    STORE_ID,
    DEPARTMENT_ID,
    STORE_TYPE,
    STORE_SIZE,
    CURRENT_TIMESTAMP() AS INSERT_DATE,
    CURRENT_TIMESTAMP() AS UPDATE_DATE

FROM ranked
WHERE rn = 1
#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
import matplotlib.pyplot as plt
from datetime import datetime 
from os import getcwd
import pandas as pd

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT
                    YEAR(TO_DATE(DATE_ID::STRING, 'YYYYMMDD')) AS YEAR,

                    CASE
                        WHEN TEMPERATURE < 0 THEN '< 0'
                        WHEN TEMPERATURE BETWEEN 0 AND 20 THEN '0-20'
                        WHEN TEMPERATURE BETWEEN 20 AND 40 THEN '20-40'
                        WHEN TEMPERATURE BETWEEN 40 AND 60 THEN '40-60'
                        ELSE '60+'
                    END AS TEMP_BUCKET,

                    SUM(STORE_WEEKLY_SALES) AS WEEKLY_SALES

                FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE

                GROUP BY
                    YEAR,
                    TEMP_BUCKET

                ORDER BY
                    YEAR,
                    TEMP_BUCKET;
            """)
        
        weekly_sales_temp_year = cur.fetch_pandas_all()

        # Pivot for bar chart
        pivot_df = weekly_sales_temp_year.pivot(index='TEMP_BUCKET', columns='YEAR', values='WEEKLY_SALES')

        # Plot
        pivot_df.plot(kind='bar')

        plt.title('Weekly Sales by Temperature Bucket and Year')
        plt.xlabel('Temperature Bucket')
        plt.ylabel('Weekly Sales')
        plt.xticks(rotation=45)
        plt.tight_layout()

        plt.show()

        plt.tight_layout()
        filename = f"walmart_sales_temp_year_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()

    finally:
        cur.close()
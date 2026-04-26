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
                S.STORE_TYPE,
                EXTRACT(MONTH FROM TO_DATE(D.STORE_DATE)) AS MNTH_NUM,
                MONTHNAME(D.STORE_DATE) AS MONTH_NAME,
                SUM(F.STORE_WEEKLY_SALES) AS TOTAL_SALES
            FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE F

            JOIN WALLMART_DB.GOLD.WALMART_STORE_DIM S
                ON F.STORE_ID = S.STORE_ID 
                AND F.DEPARTMENT_ID = S.DEPARTMENT_ID

            JOIN WALLMART_DB.GOLD.WALMART_DATE_DIM D
                ON F.DATE_ID = D.DATE_ID

            WHERE F.vrsn_end_date IS NULL

            GROUP BY 1,2,3
            ORDER BY MNTH_NUM, STORE_TYPE;
            """)
        
        weekly_sales = cur.fetch_pandas_all()

        # Clean month name spacing (Snowflake pads Month)
        weekly_sales['MONTH_NAME'] = weekly_sales['MONTH_NAME'].str.strip()

        # Sort properly
        weekly_sales = weekly_sales.sort_values('MNTH_NUM')

        # Pivot for multi-line chart
        pivot_df = weekly_sales.pivot(index='MONTH_NAME', columns='STORE_TYPE', values='TOTAL_SALES')

        # Ensure correct month order
        month_order = [
            'Jan','Feb','Mar','Apr','May','Jun',
            'Jul','Aug','Sep','Oct','Nov','Dec'
        ]
        pivot_df = pivot_df.reindex(month_order)

        plt.figure(figsize=(12,6))

        for col in pivot_df.columns:
            plt.plot(pivot_df.index, pivot_df[col], marker='o', label=f'Type {col}')

        plt.title("Weekly Sales by Store Type and Month")
        plt.xlabel("Month")
        plt.ylabel("Total Sales")

        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

        plt.tight_layout()
        filename = f"walmart_sales_storetype_month_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()

    finally:
        cur.close()
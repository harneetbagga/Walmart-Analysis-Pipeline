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
                    STORE_ID,
                    STORE_SIZE,
                    SUM(STORE_WEEKLY_SALES) AS TOTAL_SALES
                FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE
                WHERE vrsn_end_date IS NULL   -- important for SCD2
                GROUP BY STORE_ID, STORE_SIZE
                ORDER BY STORE_SIZE;
            """)
        
        weekly_sales_temp_year = cur.fetch_pandas_all()

        # Sort explicitly (very important for line/area chart)
        df = weekly_sales_temp_year.sort_values(by="STORE_SIZE")

        x = df["STORE_SIZE"]
        y = df["TOTAL_SALES"]

        plt.figure(figsize=(12,6))

        # Area chart
        plt.fill_between(x, y, alpha=0.3)

        # Line on top
        plt.plot(x, y, marker='o')

        plt.title("Weekly Sales by Store Size")
        plt.xlabel("Store Size")
        plt.ylabel("Total Sales")

        plt.tight_layout()
        filename = f"walmart_sales_store_size_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()

    finally:
        cur.close()
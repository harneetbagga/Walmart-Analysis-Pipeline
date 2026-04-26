#!/usr/bin/env python
from ..utilities.snowflake_connector import snowflake_conn
import matplotlib.pyplot as plt
from datetime import datetime 
from os import getcwd

#Path to the graphs folder
graph_folder_path = getcwd() + "/Wallmart/graphs/"

conn = snowflake_conn()

with conn.cursor() as cur:
    try:
        cur.execute("""
                SELECT 
                        STORE_ID,
                        D.DATE_ID,
                        IS_HOLIDAY,
                        SUM(STORE_WEEKLY_SALES) AS WEEKLY_SALES
                    FROM WALLMART_DB.GOLD.WALMART_FACT_TABLE F
                    JOIN WALLMART_DB.GOLD.WALMART_DATE_DIM D
                    ON F.DATE_ID=D.DATE_ID
                    WHERE VRSN_END_DATE IS NULL
                    GROUP BY STORE_ID,D.DATE_ID,IS_HOLIDAY;
                """)
        weekly_sales = cur.fetch_pandas_all()

        # Aggregate at store + holiday level
        agg_df = weekly_sales.groupby(['STORE_ID', 'IS_HOLIDAY'])['WEEKLY_SALES'].sum().reset_index()

        pivot_df = agg_df.pivot(index='STORE_ID', columns='IS_HOLIDAY', values='WEEKLY_SALES')

        # Optional: rename columns for clarity
        pivot_df.columns = ['Non-Holiday', 'Holiday']

        pivot_df['Total'] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values(by='Total', ascending=False).drop(columns='Total')

        pivot_df.plot(kind='bar')

        plt.xlabel('Store ID')
        plt.ylabel('Total Sales')
        plt.title('Walmart Sales (Sorted): Holiday vs Non-Holiday')
        plt.xticks(rotation=45)

        plt.tight_layout()
        filename = f"walmart_sales_store_holiday_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(graph_folder_path+filename, dpi=300)
        plt.show()

    finally:
        cur.close()
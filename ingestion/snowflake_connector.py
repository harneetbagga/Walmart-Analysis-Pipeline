#!/usr/bin/env python
import snowflake.connector

def snowflake_conn():
    # Gets the version
    conn = snowflake.connector.connect(
        user='harneetbgg13',
        password='bUtkim=6bovpu=bajkip',
        account='MRBPPUG-RY97098',
        warehouse='COMPUTE_WH',
        database='WALLMART_DB',
        schema='GOLD',
        role='ACCOUNTADMIN',
        )

    return conn




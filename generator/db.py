import psycopg2
import os
import time

def get_conn():
    for _ in range(30):
        try:
            return psycopg2.connect(
                host=os.environ["POSTGRES_HOST"],
                dbname=os.environ["POSTGRES_DB"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                port=5432
            )
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("Postgres not available")

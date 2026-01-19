import psycopg2
import os

def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "scooters"),
        user=os.getenv("POSTGRES_USER", "scooter"),
        password=os.getenv("POSTGRES_PASSWORD", "scooter")
    )

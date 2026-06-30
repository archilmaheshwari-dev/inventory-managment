"""
test_db.py — quick standalone check that Postgres is reachable.
Run this from your project root (same folder as .env):

    python test_db.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

import psycopg2

print("Connecting with:")
print("  HOST:", os.getenv("DB_HOST"))
print("  PORT:", os.getenv("DB_PORT", "5432"))
print("  DBNAME:", os.getenv("DB_NAME"))
print("  USER:", os.getenv("DB_USER"))

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5
    )
    print("CONNECTED OK")
    conn.close()
except Exception as e:
    print("CONNECTION FAILED:")
    print(type(e).__name__, "-", e)
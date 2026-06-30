"""
db.py — PostgreSQL connection handling
"""

import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        gssencmode="disable",
        options="-c AddressFamily=inet"
    )


@contextmanager
def get_cursor():
    """
    Context manager that handles connection + cursor + commit/rollback.
    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM patients")
            rows = cur.fetchall()
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

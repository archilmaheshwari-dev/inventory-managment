import os
import socket
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

def get_ipv4(hostname):
    """Force resolve hostname to IPv4 address"""
    results = socket.getaddrinfo(hostname, None, socket.AF_INET)
    return results[0][4][0]

def get_connection():
    host = os.getenv("DB_HOST")
    ipv4 = get_ipv4(host)
    return psycopg2.connect(
        host=ipv4,
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        gssencmode="disable"
    )

@contextmanager
def get_cursor():
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

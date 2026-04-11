import logging
import os
import urllib.parse
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
)

pw = urllib.parse.quote_plus(os.environ.get("POSTGRES_PASSWORD", ""))
user = os.environ.get("POSTGRES_USER", "axiom")
db = os.environ.get("POSTGRES_DB", "axiom")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
DATABASE_URL = os.environ.get("DATABASE_URL", f"postgresql://{user}:{pw}@{host}:{port}/{db}")

@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

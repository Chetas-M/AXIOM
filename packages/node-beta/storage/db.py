import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN", "sqlite:///./storage.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine)


def get_engine():
    return engine


def get_conn():
    if DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("get_conn() requires a PostgreSQL DATABASE_URL/POSTGRES_DSN")
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 is required for get_conn()") from exc
    return psycopg2.connect(DATABASE_URL)

import psycopg2
from app.core.config import DB_CONFIG


def get_connection():
    """PostgreSQL 연결 객체를 반환한다."""
    return psycopg2.connect(**DB_CONFIG)

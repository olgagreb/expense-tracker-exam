import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "expense_exam")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    if not password:
        raise RuntimeError("DB_PASSWORD порожній. Додайте пароль у .env")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def init_db():
    conn = get_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
                    expense_date DATE NOT NULL,
                    category_id INT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                    description TEXT,
                    currency VARCHAR(10) DEFAULT 'UAH'
                );
            """)
    finally:
        conn.close()

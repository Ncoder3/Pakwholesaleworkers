import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    """Establishes connection to Railway PostgreSQL database."""
    if not DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"[DB ERROR] Connection failed: {e}")
        return None

def init_db():
    """Applies schema on startup if running on cloud."""
    conn = get_db_connection()
    if not conn:
        return
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print("[DB SUCCESS] Database schema initialized.")
        except Exception as e:
            conn.rollback()
            print(f"[DB ERROR] Schema initialization failed: {e}")
        finally:
            conn.close()
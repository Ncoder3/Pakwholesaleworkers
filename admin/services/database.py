import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

import psycopg2

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # 1. Create customers table if it doesn't exist yet
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    phone VARCHAR(50),
                    city VARCHAR(100),
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Add the unique constraint safely without throwing errors if it already exists
            cur.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'unique_customer_phone'
                    ) THEN 
                        ALTER TABLE customers ADD CONSTRAINT unique_customer_phone UNIQUE (phone);
                    END IF;
                END $$;
            """)

            conn.commit()
            print("PostgreSQL database initialized and constraints updated successfully.")
        except Exception as e:
            conn.rollback()
            print(f"Database initialization error: {e}")
        finally:
            conn.close()

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
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
    """Applies schema updates, fixes customer_id constraints, and runs auto-migrations."""
    conn = get_db_connection()
    if not conn:
        print("[DB WARN] DATABASE_URL not set. Skipping DB initialization.")
        return

    try:
        with conn.cursor() as cur:
            # 1. Execute schema.sql if present
            schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, "r", encoding="utf-8") as f:
                    sql = f.read()
                if sql.strip():
                    cur.execute(sql)
                    print("[DB SUCCESS] Executed schema.sql.")

            # 2. Ensure customers table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    phone VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. Add missing columns safely
            columns_to_add = [
                ("city", "VARCHAR(100)"),
                ("address", "TEXT"),
                ("customer_id", "VARCHAR(100)")
            ]
            for col_name, col_type in columns_to_add:
                cur.execute(f"""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='customers' AND column_name='{col_name}'
                        ) THEN 
                            ALTER TABLE customers ADD COLUMN {col_name} {col_type};
                        END IF;
                    END $$;
                """)

            # 4. Remove NOT NULL constraint from customer_id if it exists
            cur.execute("""
                DO $$ 
                BEGIN 
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='customers' 
                        AND column_name='customer_id' 
                        AND is_nullable='NO'
                    ) THEN 
                        ALTER TABLE customers ALTER COLUMN customer_id DROP NOT NULL;
                    END IF;
                END $$;
            """)

            # 5. Add unique constraint on phone safely
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
        print("[DB SUCCESS] Database schema initialized and migrated successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] Database initialization failed: {e}")
    finally:
        conn.close()
import os
import threading
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

db_pool = None
db_alive = True
db_fail_count = 0
db_lock = threading.Lock()

def get_db_connection():
    global db_pool, db_alive, db_fail_count
    if not db_alive:
        return None
    
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not set")
        return None

    with db_lock:
        if not db_pool:
            try:
                db_pool = pool.ThreadedConnectionPool(
                    1, 20,
                    db_url,
                    connect_timeout=10
                )
                print("Database connection pool created.")
                db_fail_count = 0
            except Exception as e:
                db_fail_count += 1
                print(f"Error creating connection pool ({db_fail_count}): {e}")
                if db_fail_count > 3:
                    print("Disabling DB attempts (Circuit Breaker).")
                    db_alive = False
                try:
                    return psycopg2.connect(db_url, connect_timeout=10)
                except:
                    return None
    
    try:
        conn = db_pool.getconn()
        return conn
    except Exception as e:
        print(f"Pool delivery error: {e}")
        return None

def return_db_connection(conn):
    if not conn: return
    try:
        if db_pool:
            db_pool.putconn(conn)
        else:
            conn.close()
    except Exception as e:
        print(f"Connection cleanup error: {e}")
        try: conn.close()
        except: pass

def init_db():
    try:
        conn = get_db_connection()
        if not conn:
            print("Skipping DB Init: Database unreachable.")
            return
        try:
            cur = conn.cursor()
            # Stock Cache Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_cache (
                    symbol TEXT PRIMARY KEY,
                    data JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Users Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nickname TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Portfolio Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    symbol TEXT NOT NULL,
                    entry_price NUMERIC NOT NULL,
                    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            print("Database initialized successfully.")
        finally:
            return_db_connection(conn)
    except Exception as e:
        print(f"init_db failed: {e}")

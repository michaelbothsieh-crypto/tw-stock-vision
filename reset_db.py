
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def reset_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL not found.")
        return

    try:
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        
        print("Resetting database tables...")
        
        # TRUNCATE tables to clear data but keep structure
        tables = ['stock_cache', 'portfolio_items', 'users']
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
                print(f"Table '{table}' cleared.")
            except Exception as te:
                print(f"Could not clear table '{table}': {te}")
                conn.rollback()
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database reset complete.")
        
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    reset_db()

import os
import json
from api.db import get_db_connection, return_db_connection

def clear_cache():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return
    try:
        cur = conn.cursor()
        print("Clearing cache for 2337...")
        cur.execute("DELETE FROM stock_cache WHERE symbol = '2337'")
        print("Clearing cache for 2330...")
        cur.execute("DELETE FROM stock_cache WHERE symbol = '2330'")
        # Optional: Clear everything if data leakage was widespread
        # cur.execute("TRUNCATE TABLE stock_cache")
        conn.commit()
        cur.close()
        print("Cache cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        return_db_connection(conn)

if __name__ == "__main__":
    clear_cache()

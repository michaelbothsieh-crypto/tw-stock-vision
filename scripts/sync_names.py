
import os
import sys
import twstock
import requests
import pandas as pd
from io import StringIO

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Manually load .env
try:
    with open(os.path.join(parent_dir, '.env'), 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

from api.db import get_db_connection, return_db_connection

def fetch_isin_stocks(mode=5):
    """
    Fetch stocks from TWSE ISIN website.
    Mode 2: Listed (上市)
    Mode 4: OTC (上櫃)
    Mode 5: Emerging (興櫃)
    """
    url = f"https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}"
    try:
        res = requests.get(url)
        res.encoding = 'ms950' 
        
        dfs = pd.read_html(StringIO(res.text))
        if not dfs: return {}
        
        df = dfs[0]
        df.columns = df.iloc[0]
        df = df[1:]
        
        stock_dict = {}
        for index, row in df.iterrows():
            try:
                code_name = str(row.iloc[0])
                parts = code_name.split()
                if len(parts) >= 2:
                    code = parts[0]
                    name = parts[1]
                    stock_dict[code] = name
                    
                    if len(code) == 5 and code.startswith('0'):
                        alias = code[1:]
                        if alias not in stock_dict:
                            stock_dict[alias] = name
            except:
                continue
        return stock_dict
    except Exception as e:
        print(f"Error fetching ISIN mode {mode}: {e}")
        return {}

def sync_stock_names():
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return

    print("Starting stock names sync...")
    names = {}
    
    # 1. Base: twstock (Listed + OTC)
    print("Loading from twstock...", flush=True)
    try:
        for code, stock in twstock.codes.items():
            if stock.type in ['股票', 'ETF']:
                names[code] = stock.name
    except Exception as e:
        print(f"Error loading from twstock: {e}")

    # 2. Extension: Emerging Stocks (興櫃) from ISIN Mode 5
    print("Fetching Emerging stocks from ISIN...", flush=True)
    emerging = fetch_isin_stocks(5)
    print(f"Fetched {len(emerging)} emerging stocks.", flush=True)
    names.update(emerging)
    
    # 3. Listed/OTC from ISIN (Refresher)
    print("Fetching Listed/OTC updates from ISIN...", flush=True)
    listed = fetch_isin_stocks(2)
    otc = fetch_isin_stocks(4)
    names.update(listed)
    names.update(otc)

    print(f"Total unique stocks found: {len(names)}")

    # Batch Insert/Upsert
    try:
        cur = conn.cursor()
        # Prepare list of tuples
        data_tuples = [(code, name, 'STOCK') for code, name in names.items()]
        
        # Use execute_values for speed if available, or just loop for simplicity in this scale
        # Upsert: ON CONFLICT DO UPDATE
        upsert_query = """
            INSERT INTO stock_names (symbol, name, type, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (symbol) DO UPDATE 
            SET name = EXCLUDED.name, updated_at = NOW();
        """
        
        print("Upserting to database...", flush=True)
        # Using executemany for batch performance
        cur.executemany(upsert_query, data_tuples)
        conn.commit()
        print("Sync complete.")
        cur.close()
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        return_db_connection(conn)

if __name__ == "__main__":
    sync_stock_names()

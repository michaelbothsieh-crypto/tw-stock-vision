
import os
import sys
import time

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
from api.services.stock_service import StockService
from api.constants import TW_STOCK_NAMES

def get_tracked_stocks():
    """
    Get list of stocks to update.
    Includes:
    1. Stocks in user portfolios
    2. Fixed list of important stocks (Hot stocks)
    """
    conn = get_db_connection()
    if not conn: return []
    
    symbols = set()
    
    try:
        cur = conn.cursor()
        # 1. Portfolio stocks
        cur.execute("SELECT DISTINCT symbol FROM portfolio_items")
        rows = cur.fetchall()
        for r in rows:
            symbols.add(r[0])
            
        cur.close()
    except Exception as e:
        print(f"Error fetching portfolio stocks: {e}")
    finally:
        return_db_connection(conn)

    # 2. Hot Stocks (Taiwan)
    hot_stocks = [
        "2330", "2317", "2454", "2603", "2881", "2308", "2382", "2882", "3711", "0050", "0056", "00878", "00919", "00929"
    ]
    for s in hot_stocks:
        symbols.add(s)

    return list(symbols)

def update_market_data():
    print("Starting market data update...", flush=True)
    
    # Ensure constants are loaded? 
    # Actually StockService uses TW_STOCK_NAMES, which is currently empty in api.constants because we removed the auto-load.
    # We should probably load it from DB first if we want StockService to work perfectly with names, 
    # but StockService might fetch name from TVS/Yahoo anyway.
    # Let's try to populate TW_STOCK_NAMES from DB first.
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT symbol, name FROM stock_names")
            rows = cur.fetchall()
            for r in rows:
                TW_STOCK_NAMES[r[0]] = r[1]
            print(f"Loaded {len(TW_STOCK_NAMES)} names from DB.", flush=True)
            cur.close()
        except Exception as e:
            print(f"Error loading names from DB: {e}")
        finally:
            return_db_connection(conn)

    stocks = get_tracked_stocks()
    print(f"Updating {len(stocks)} stocks...", flush=True)

    for symbol in stocks:
        try:
            print(f"Updating {symbol}...", flush=True)
            # flush=True forces fetch from external sources
            data = StockService.get_stock_details(symbol, flush=True)
            if data:
                print(f"  -> Success: {data.get('price')}", flush=True)
            else:
                print(f"  -> Failed", flush=True)
            
            # Be nice to external APIs
            time.sleep(1) 
        except Exception as e:
            print(f"Error updating {symbol}: {e}")

    print("Market data update complete.")

if __name__ == "__main__":
    update_market_data()

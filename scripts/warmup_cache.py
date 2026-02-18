import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from api.services.stock_service import StockService
from api.db import get_db_connection, return_db_connection

def warmup():
    print(f"[{datetime.now()}] Starting Market Data Warmup...")
    
    # 1. Warmup TW market
    print(f"[{datetime.now()}] Warming up TW Trending stocks...")
    tw_stocks = StockService.get_market_trending("TW")
    print(f"[{datetime.now()}] TW Warmup complete. Found {len(tw_stocks)} stocks.")
    
    # 2. Warmup US market
    print(f"[{datetime.now()}] Warming up US Trending stocks...")
    us_stocks = StockService.get_market_trending("US")
    print(f"[{datetime.now()}] US Warmup complete. Found {len(us_stocks)} stocks.")
    
    print(f"[{datetime.now()}] Warmup sequence finished.")

if __name__ == "__main__":
    warmup()

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from api.services.stock_service import StockService

def benchmark():
    print(f"[{datetime.now()}] Running Performance Benchmark...")
    
    start_time = time.time()
    results = StockService.get_market_trending("TW")
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"[{datetime.now()}] Benchmark Result: Fetched {len(results)} stocks in {duration:.2f} seconds.")
    
    if duration < 5:
        print("Performance is GOOD ( < 5s )")
    elif duration < 15:
        print("Performance is ACCEPTABLE ( < 15s )")
    else:
        print("Performance is still SLOW ( > 15s )")

if __name__ == "__main__":
    benchmark()

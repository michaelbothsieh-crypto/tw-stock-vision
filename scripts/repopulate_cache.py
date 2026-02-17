
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.stock_service import StockService

def repopulate():
    print("Repopulating cache...")
    symbols = ["2330", "2317", "2454", "2308", "2382", "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"]
    
    for symbol in symbols:
        print(f"Fetching {symbol}...")
        try:
            # flush=True forces a fetch and cache
            data = StockService.get_stock_details(symbol, flush=True)
            if data:
                print(f"Successfully cached {symbol}")
            else:
                print(f"Failed to fetch {symbol}")
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

if __name__ == "__main__":
    repopulate()

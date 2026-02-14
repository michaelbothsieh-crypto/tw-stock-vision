from api.scrapers import fetch_from_yfinance, format_market_cap
import json
import re

def verify_fix():
    print("=== Testing US Stocks (Expected: T/B, AI Metrics Non-Zero) ===")
    for sym in ["NVDA", "AAPL", "TSLA"]:
        data = fetch_from_yfinance(sym)
        if data:
            print(f"[{sym}] MCap: {data.get('marketCap')}, F-Score: {data.get('fScore')}, Z-Score: {data.get('zScore')}")
        else:
            print(f"[{sym}] Failed")

    print("\n=== Testing TW Stocks (Expected: 兆/億) ===")
    for sym in ["2330", "2454", "2408"]:
        data = fetch_from_yfinance(sym)
        if data:
            print(f"[{sym}] MCap: {data.get('marketCap')}, F-Score: {data.get('fScore')}, Z-Score: {data.get('zScore')}")
        else:
            print(f"[{sym}] Failed")

if __name__ == "__main__":
    verify_fix()

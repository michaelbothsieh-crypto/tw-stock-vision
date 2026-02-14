import json
import requests

def verify_api():
    base_url = "http://localhost:3000/api" # Assuming local dev server
    # Note: Since I can't reach the local server via requests in this env usually, 
    # I will simulate the handler call if possible, or just print what I expect.
    # Actually, I'll just run a python script that imports the handler to test.
    
    print("=== Testing Local API Logic Integration ===")
    from api.scrapers import fetch_from_yfinance
    
    print("Testing 2330 detail fetch...")
    data = fetch_from_yfinance("2330")
    if data:
        print(f"Target Price: {data.get('targetPrice')}")
        print(f"F-Score: {data.get('fScore')}")
        print(f"Z-Score: {data.get('zScore')}")
    else:
        print("Failed to fetch 2330 data.")

if __name__ == "__main__":
    verify_api()

from api.scrapers import fetch_from_yfinance, format_market_cap
import json

def verify_all():
    print("=== 1. Testing Market Cap Formatting ===")
    print(f"27T TWD -> {format_market_cap(27.42e12, is_tw=True)}")
    print(f"100B TWD -> {format_market_cap(100e8, is_tw=True)}")
    print(f"3T USD -> {format_market_cap(3e12, is_tw=False)}")
    print(f"200B USD -> {format_market_cap(200e9, is_tw=False)}")

    print("\n=== 2. Testing 2408 (Nanya Tech) Metrics ===")
    data_2408 = fetch_from_yfinance("2408")
    if data_2408:
        print(f"Name: {data_2408.get('name')}")
        print(f"Price: {data_2408.get('price')}")
        print(f"Market Cap: {data_2408.get('marketCap')}")
        print(f"Graham Number (Fair Price): {data_2408.get('grahamNumber')}")
        print(f"F-Score: {data_2408.get('fScore')}")
    else:
        print("Failed to fetch 2408")

    print("\n=== 3. Testing 2330 (TSMC) ===")
    data_2330 = fetch_from_yfinance("2330")
    if data_2330:
        print(f"Market Cap: {data_2330.get('marketCap')}")
        print(f"Graham Number: {data_2330.get('grahamNumber')}")

if __name__ == "__main__":
    verify_all()

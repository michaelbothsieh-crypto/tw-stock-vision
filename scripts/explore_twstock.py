import twstock
import json

print("--- twstock Deep Dive ---")

# 1. Real-time Data
print("\n[1] Real-time Data (2330 台積電):")
try:
    realtime = twstock.realtime.get('2330')
    if realtime['success']:
        print(f"Info: {realtime['info']['name']} ({realtime['info']['code']})")
        print(f"Time: {realtime['info']['time']}")
        print(f"Realtime Price: {realtime['realtime']['latest_trade_price']}")
        print(f"Best Bid: {realtime['realtime']['best_bid_price']}")
        print(f"Best Ask: {realtime['realtime']['best_ask_price']}")
        
        # Check what else is in info
        print(f"Full Info Keys: {list(realtime['info'].keys())}")
    else:
        print(f"Failed to get real-time data: {realtime['rtmessage']}")
except Exception as e:
    print(f"Real-time fetch error: {e}")

# 2. Historical Data
print("\n[2] Historical Data (Last 3 days for 2330):")
try:
    stock = twstock.Stock('2330')
    history = stock.fetch_from(2023, 10) # Fetch recent just to be sure, or just fetch()
    # Let's just fetch last 5 entries to be quick
    data = stock.fetch_31()
    if data:
        for entry in data[-3:]:
             print(f"Date: {entry.date}, Close: {entry.close}, High: {entry.high}, Low: {entry.low}, Volume: {entry.capacity}")
    else:
        print("No historical data returned.")
except Exception as e:
    print(f"History fetch error: {e}")

# 3. Stock Metadata
print("\n[3] Static Metadata (2330):")
if '2330' in twstock.codes:
    info = twstock.codes['2330']
    print(f"Name: {info.name}")
    print(f"Type: {info.type}")
    print(f"Market: {info.market}")
    print(f"Code: {info.code}")
    # Inspect object attributes
    print(f"Start Date: {info.start}")
    print(f"Group: {info.group}")
else:
    print("Metadata not found.")

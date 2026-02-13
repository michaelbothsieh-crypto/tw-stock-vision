from tvscreener import TVScreener
import json

ss = TVScreener()
# Fetch a sample stock (e.g., TSLA or 2330) to see all available keys
df = ss.get_technical_indicators(symbol="2330", exchange="TWSE", interval="1d")
# Convert first row to dict and print keys
if not df.empty:
    print(json.dumps(list(df.iloc[0].to_dict().keys()), indent=2))
else:
    print("No data found")

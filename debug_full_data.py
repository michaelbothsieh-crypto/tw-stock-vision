import tvscreener as tvs
import sys

print("--- Start Debug ---")
try:
    ss = tvs.StockScreener()
    ss.set_markets(tvs.Market.AMERICA)
    # Just try to get anything
    print("Fetching US Data...")
    df = ss.get()
    print(f"US Data Shape: {df.shape}")
    if not df.empty:
        print("US Columns:", list(df.columns))
except Exception as e:
    print(f"US Error: {e}")

try:
    ss_tw = tvs.StockScreener()
    ss_tw.set_markets(tvs.Market.TAIWAN)
    print("Fetching TW Data...")
    df_tw = ss_tw.get()
    print(f"TW Data Shape: {df_tw.shape}")
    if not df_tw.empty:
        print("TW Columns:", list(df_tw.columns))
except Exception as e:
    print(f"TW Error: {e}")

print("--- End Debug ---")
sys.stdout.flush()

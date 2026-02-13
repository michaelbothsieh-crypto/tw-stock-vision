import tvscreener as tvs
from tvscreener import StockScreener, StockField
import json

def inspect_stock(symbol, market):
    ss = StockScreener()
    ss.set_markets(market)
    # Search for the symbol
    # Note: tvscreener retrieval might return multiple results.
    # We want to find the exact match if possible, or print the first one.
    
    # In v0.2.0, commonly we just get everything and filter, or use a specific search method if available.
    # Let's try to get a broad list and filter, or use the default 'get' which might return top stocks.
    # Actually, let's look at what `ss.get()` returns with default settings to see if we can filter.
    
    # Wait, fetching everything is slow.
    # Let's try to add a filter if possible.
    # ss.add_filter(Filter('ticker', 'match', symbol)) # Hypothetical
    
    # Let's just fetch top 10 and print keys to see available fields.
    df = ss.get()
    if not df.empty:
        print(f"--- Data Keys for {market} ---")
        print(df.columns.tolist())
        print("--- Sample Data ---")
        print(df.iloc[0].to_dict())
    else:
        print(f"No data found for {market}")

print("Inspecting TWSE...")
inspect_stock("2330", tvs.Market.TAIWAN)

print("\nInspecting US...")
inspect_stock("AAPL", tvs.Market.AMERICA)

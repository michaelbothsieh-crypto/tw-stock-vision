
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import pandas as pd
import json

def test_tvs(symbol):
    print(f"Testing TV for {symbol}...")
    ss = StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    
    # Select a few fields
    ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE)
    
    # Try with filter
    ss.add_filter(StockField.NAME, tvs.FilterOperator.EQUAL, symbol)
    df = ss.get()
    print("Filter search results:")
    print(df)
    
    # Try broad search
    print("\nBroad search (all TW stocks snippet):")
    ss2 = StockScreener()
    ss2.set_markets(tvs.Market.TAIWAN)
    df2 = ss2.get()
    match = df2[df2['Symbol'].str.contains(symbol, case=False, na=False)]
    print(f"Broad search matches for {symbol}:")
    print(match)

if __name__ == "__main__":
    test_tvs("2330")

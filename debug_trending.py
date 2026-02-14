import tvscreener as tvs
from tvscreener import StockScreener, StockField
import pandas as pd
import json

def test_trending():
    print("Testing Market Trending Logic...")
    try:
        ss = StockScreener()
        ss.set_markets(tvs.Market.TAIWAN)
        ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE_PERCENT, StockField.TECHNICAL_RATING)
        ss.sort_by(StockField.TECHNICAL_RATING, ascending=False)
        df = ss.get()
        
        print(f"Row count: {len(df)}")
        if not df.empty:
            print("First 3 rows:")
            print(df.head(3).to_dict(orient='records'))
        else:
            print("DataFrame is EMPTY!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trending()

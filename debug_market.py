import tvscreener as tvs
from tvscreener import StockScreener, StockField
import json

def debug_market():
    print("--- Debugging Market Trending ---")
    try:
        ss = StockScreener()
        ss.set_markets(tvs.Market.TAIWAN)
        ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE_PERCENT, StockField.TECHNICAL_RATING)
        ss.sort_by(StockField.TECHNICAL_RATING, ascending=False)
        df = ss.get()
        
        if df.empty:
            print("StockScreener returned empty DataFrame")
            return

        print("DataFrame Columns found:", list(df.columns))
        print("First Row Raw Keys:", list(df.iloc[0].to_dict().keys()))
        print("First Row Data Preview:")
        print(df.head(3).to_string())
        
        # Test the extraction logic used in api/index.py
        results = []
        for i, (_, row) in enumerate(df.head(3).iterrows()):
            data = {
                "symbol": row.get('Name', ''),
                "description": row.get('Description', ''),
                "price": row.get('Price', 0),
                "changePercent": row.get('Change %', 0),
                "rating": row.get('Technical Rating', 0)
            }
            results.append(data)
            print(f"Row {i} extraction: {data}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_market()

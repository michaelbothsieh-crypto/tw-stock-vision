import yfinance as yf
import json
import tvscreener as tvs
from tvscreener import StockScreener, StockField

def diagnose_2408():
    print("=== Diagnosing 2408.TW ===")
    for ticker in ["2408.TW", "2408.TWO"]:
        print(f"\nTrying {ticker}...")
        t = yf.Ticker(ticker)
        info = t.info
        if info:
            print(f"Long Name: {info.get('longName')}")
            print(f"Current Price: {info.get('currentPrice')}")
            print(f"Target Mean: {info.get('targetMeanPrice')}")
            print(f"Target Median: {info.get('targetMedianPrice')}")
            print(f"Recommendation: {info.get('recommendationKey')}")
        else:
            print(f"No info for {ticker}")

def diagnose_market_trending():
    print("\n=== Diagnosing Market Trending API Logic ===")
    try:
        ss = StockScreener()
        ss.set_markets(tvs.Market.TAIWAN)
        ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE_PERCENT, StockField.TECHNICAL_RATING)
        ss.sort_by(StockField.TECHNICAL_RATING, ascending=False)
        df = ss.get()
        print(f"DataFrame Size: {len(df)}")
        if not df.empty:
            print("First 3 Rows (Raw):")
            print(df.head(3).to_dict(orient='records'))
            
            # Simulated parsing logic
            for _, row in df.head(3).iterrows():
                raw_name = str(row.get('Name', ''))
                raw_symbol = str(row.get('Symbol', ''))
                symbol = raw_name if raw_name.isdigit() else raw_symbol.split(':')[-1]
                print(f"Parsed Symbol: {symbol} (from Name='{raw_name}', Symbol='{raw_symbol}')")
    except Exception as e:
        print(f"Market Trending Error: {e}")

if __name__ == "__main__":
    diagnose_2408()
    diagnose_market_trending()

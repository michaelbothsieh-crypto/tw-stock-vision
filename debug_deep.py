import tvscreener as tvs
from tvscreener import StockScreener, StockField
import yfinance as yf
import json
import pandas as pd

def test_market_explorer_data():
    print("=== 1. Testing TVScreener Trending (TAIWAN) ===")
    try:
        ss = StockScreener()
        ss.set_markets(tvs.Market.TAIWAN)
        ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE_PERCENT, StockField.TECHNICAL_RATING)
        ss.sort_by(StockField.TECHNICAL_RATING, ascending=False)
        df = ss.get()
        print(f"Columns found: {df.columns.tolist()}")
        if not df.empty:
            print(f"Sample data (row 0): {df.iloc[0].to_dict()}")
        else:
            print("Trending DataFrame is EMPTY!")
    except Exception as e:
        print(f"TVS Trending Error: {e}")

def test_stock_details(symbol="2330.TW"):
    print(f"\n=== 2. Testing Stock Details (yfinance: {symbol}) ===")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"Current Price: {info.get('currentPrice')}")
        print(f"Target Mean Price: {info.get('targetMeanPrice')}")
        print(f"Recommendation: {info.get('recommendationKey')}")
        # Check financial fields needed for F-Score/Z-Score
        print(f"Key Financials (partial):")
        keys = ['totalRevenue', 'netIncome', 'totalAssets', 'totalLiabilities', 'operatingCashflow']
        fin_data = {k: info.get(k) for k in keys}
        print(json.dumps(fin_data, indent=2))
    except Exception as e:
        print(f"yfinance Detail Error: {e}")

if __name__ == "__main__":
    test_market_explorer_data()
    test_stock_details("2330.TW")

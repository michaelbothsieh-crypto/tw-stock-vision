import sys
import os
import json

# Add current directory to path
sys.path.append(os.getcwd())

from api.scrapers import fetch_from_yfinance, process_tvs_row
import tvscreener as tvs
from tvscreener import StockScreener, StockField

def test_lookup(symbol):
    print(f"--- Testing {symbol} ---")
    
    # 1. Test TV
    try:
        ss = StockScreener()
        ss.set_markets(tvs.Market.TAIWAN if symbol.isdigit() else tvs.Market.AMERICA)
        ss.search(symbol)
        ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE, StockField.CHANGE_PERCENT, 
                  StockField.VOLUME, StockField.MARKET_CAPITALIZATION, StockField.TECHNICAL_RATING,
                  StockField.PIOTROSKI_F_SCORE_TTM, StockField.BASIC_EPS_TTM, StockField.AVERAGE_TRUE_RANGE_14)
        df = ss.get()
        if not df.empty:
            raw_row = df.iloc[0].to_dict()
            print("TV Raw Row Keys:", raw_row.keys())
            data = process_tvs_row(raw_row, symbol)
            print("Processed TV Data (F-Score):", data.get('fScore'))
            print("Processed TV Data (ATR):", data.get('atr'))
        else:
            print("TV returned empty for", symbol)
    except Exception as e:
        print("TV Error:", e)

    # 2. Test yfinance
    try:
        yf_data = fetch_from_yfinance(symbol)
        if yf_data:
            print("yfinance Data (Price):", yf_data.get('price'))
            print("yfinance Data (F-Score Est):", yf_data.get('fScore'))
            print("yfinance Data (Z-Score Est):", yf_data.get('zScore'))
        else:
            print("yfinance returned None for", symbol)
    except Exception as e:
        print("yfinance Error:", e)

if __name__ == "__main__":
    results = {}
    for sym in ["2330", "AAPL"]:
        # 1. Test TV
        tv_info = {}
        try:
            ss = StockScreener()
            ss.set_markets(tvs.Market.TAIWAN if sym.isdigit() else tvs.Market.AMERICA)
            ss.search(sym)
            df = ss.get()
            if not df.empty:
                raw_row = df.iloc[0].to_dict()
                processed = process_tvs_row(raw_row, sym)
                tv_info = {"raw_keys": list(raw_row.keys()), "processed": processed}
        except Exception as e:
            tv_info = {"error": str(e)}
        
        # 2. Test yfinance
        yf_info = {}
        try:
            yf_info = fetch_from_yfinance(sym)
        except Exception as e:
            yf_info = {"error": str(e)}
            
        results[sym] = {"tv": tv_info, "yf": yf_info}
    
    with open("test_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Results written to test_output.json")

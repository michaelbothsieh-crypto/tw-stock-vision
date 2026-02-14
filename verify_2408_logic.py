from api.scrapers import fetch_from_yfinance, process_tvs_row
from tvscreener import StockScreener, StockField
import tvscreener as tvs
import json

def test_2408_logic_direct():
    symbol = "2408"
    print(f"=== Testing Direct Logic for {symbol} ===")
    
    # 1. Fetch from yfinance (The source we want to protect)
    yf_data = fetch_from_yfinance(symbol)
    print(f"YFinance Target: {yf_data.get('targetPrice')}")
    
    # 2. Fetch from TVS (The potential wrong source)
    ss = StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    ss.search(symbol)
    ss.select(StockField.NAME, StockField.PRICE_TARGET_AVERAGE)
    df = ss.get()
    
    data = None
    if not df.empty:
        raw_row = df.iloc[0].to_dict()
        data = process_tvs_row(raw_row, symbol)
        print(f"TVS Target: {data.get('targetPrice')}")
    
    # 3. Simulate Logic from index.py
    if data and yf_data:
        keys_to_merge = ['targetPrice']
        is_tw = symbol.isdigit()
        for k in keys_to_merge:
            force_yf = False
            if k == 'targetPrice' and is_tw and yf_data.get('targetPrice'):
                force_yf = True
            
            if force_yf or data.get(k) is None or data.get(k) == 0:
                val = yf_data.get(k)
                if val is not None:
                    data[k] = val
                    print(f"Merged {k} from YF (force_yf={force_yf})")
    
    print(f"FINAL RESULT TARGET PRICE: {data.get('targetPrice') if data else 'N/A'}")

if __name__ == "__main__":
    test_2408_logic_direct()

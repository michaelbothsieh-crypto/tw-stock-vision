import tvscreener as tvs
from tvscreener import StockScreener, StockField
import json

def verify_trending_logic():
    print("Testing Trending Symbol Extraction...")
    ss = StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    ss.select(StockField.NAME, StockField.SYMBOL)
    df = ss.get()
    
    if not df.empty:
        results = []
        for _, row in df.head(5).iterrows():
            raw_name = str(row.get('Name', ''))
            raw_symbol = str(row.get('Symbol', ''))
            symbol = raw_name if raw_name.isdigit() else raw_symbol.split(':')[-1]
            if not symbol: symbol = raw_symbol
            results.append({"raw_name": raw_name, "raw_symbol": raw_symbol, "parsed_symbol": symbol})
        
        print(json.dumps(results, indent=2))
    else:
        print("TVS returned empty DF.")

if __name__ == "__main__":
    verify_trending_logic()

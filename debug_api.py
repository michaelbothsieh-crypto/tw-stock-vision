import sys
import os
import math
import json
import re

# Add api to path
sys.path.append(os.path.join(os.getcwd(), 'api'))

try:
    import tvscreener as tvs
    from tvscreener import StockScreener, StockField
    import pandas as pd
    
    def test_search(symbol):
        print(f"--- Testing Search for: {symbol} ---")
        ss = StockScreener()
        
        is_us_stock = bool(re.search(r'[A-Za-z]', symbol))
        if is_us_stock:
            ss.set_markets(tvs.Market.AMERICA)
        else:
            ss.set_markets(tvs.Market.TAIWAN)
            
        print(f"Setting search: {symbol}")
        ss.search(symbol)
        
        ss.select(
            StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, 
            StockField.CHANGE, StockField.CHANGE_PERCENT, 
            StockField.EXCHANGE
        )
        
        print("Executing get()...")
        df = ss.get()
        
        if df.empty:
            print("ERROR: Result is EMPTY!")
            # Try without search() but with filter
            print("Trying with filter instead...")
            ss2 = StockScreener()
            if is_us_stock: ss2.set_markets(tvs.Market.AMERICA)
            else: ss2.set_markets(tvs.Market.TAIWAN)
            ss2.add_filter(StockField.NAME, tvs.FilterOperator.MATCH, symbol)
            df2 = ss2.get()
            if df2.empty:
                 print("ERROR: Filter also empty!")
            else:
                 print(f"SUCCESS with filter! Found: {df2.iloc[0]['Name']}")
        else:
            print(f"SUCCESS! Found {len(df)} rows.")
            print(f"First result: {df.iloc[0].to_dict()}")

    test_search('2330')
    test_search('TSLA')

except Exception as e:
    import traceback
    traceback.print_exc()

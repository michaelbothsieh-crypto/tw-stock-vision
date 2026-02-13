import sys
import os
try:
    import tvscreener as tvs
    from tvscreener import StockScreener, StockField
    print("tvscreener imported successfully")
    
    ss = StockScreener()
    
    # Try finding Taiwan in Market enum if possible, or use string
    # ss.set_markets('taiwan') 
    
    # Check if 'taiwan' is a valid market string or if we need the enum
    # README says ss.set_markets(tvs.Market.AMERICA)
    # Let's try to find TAIWAN in Market enum
    try:
        ss.set_markets(tvs.Market.TAIWAN)
        print("Set market to TAIWAN via Enum")
    except AttributeError:
        print("Market.TAIWAN not found, trying string 'taiwan'")
        try:
            ss.set_markets('taiwan')
        except Exception as e:
            print(f"Failed to set market 'taiwan': {e}")
            # print available attributes to debug
            # print(dir(ss))

    # Filter by ticker
    # README: ss.where(StockField.price > 50)
    # We need to find the specific field for Ticker or Symbol.
    # Often it is 'ticker', 'name', or 'description'.
    # Let's search for it.
    
    # search = StockField.search('ticker')
    # print("Search results for 'ticker':", search)
    
    # Assuming we want to search for '2330'
    # Use the filter method if available or where
    # ss.where(StockField.TICKER == '2330') # Guessing Field name
    
    # Let's just get the top stocks in Taiwan for now to verify connectivity
    # without specific ticker filter first
    
    df = ss.get()
    print(f"Fetch successful. Rows: {len(df)}")
    if not df.empty:
        print("Columns:", df.columns.tolist())
        print("First row:", df.iloc[0].to_dict())
        
        # Now try to verify if we can filter by 'Ticker' column in the DF
        # usually columns are 'symbol', 'name', ...
        if 'symbol' in df.columns:
            tsmc = df[df['symbol'].str.contains('2330')]
            if not tsmc.empty:
                print("Found 2330 in top results:", tsmc.iloc[0].to_dict())
            else:
                print("2330 not in top results")

except ImportError:
    print("Failed to import tvscreener")
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()

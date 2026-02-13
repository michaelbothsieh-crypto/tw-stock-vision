import tvscreener as tvs
from tvscreener import StockScreener, StockField

with open('inspection_result.txt', 'w', encoding='utf-8') as f:
    try:
        f.write("=== Library Info ===\n")
        f.write(f"Version: {tvs.__version__ if hasattr(tvs, '__version__') else 'Unknown'}\n")
        
        f.write("\n=== Available StockFields (Indicators & Data) ===\n")
        # Listing attributes of StockField to see what we can screen for
        fields = [attr for attr in dir(StockField) if not attr.startswith('__')]
        # Print first 50 to avoid flooding, or categorize
        f.write(f"Total Fields: {len(fields)}\n")
        f.write(f"Sample Fields: {fields[:50]}\n")
        
        f.write("\n=== Sample Data Fetch (2330) ===\n")
        ss = StockScreener()
        ss.set_markets(tvs.Market.TAIWAN)
        # Try to filter specifically to get a rich dataset
        df = ss.get()
        
        if not df.empty:
            f.write("\nColumns available in response:\n")
            f.write(str(df.columns.tolist()) + "\n")
            
            # specific 2330 check
            k = '2330'
            # Adjust for column name potentially being 'Symbol' or 'Ticker'
            col = 'Symbol' if 'Symbol' in df.columns else 'Ticker'
            row = df[df[col].astype(str).str.contains(k)]
            
            if not row.empty:
                f.write(f"\nData for {k}:\n")
                f.write(str(row.iloc[0].to_dict()) + "\n")
            else:
                f.write(f"\n{k} not found in top results. Showing first result:\n")
                f.write(str(df.iloc[0].to_dict()) + "\n")

    except Exception as e:
        f.write(f"Error: {e}\n")

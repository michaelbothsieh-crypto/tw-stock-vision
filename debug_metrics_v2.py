import yfinance as yf
import json

def check_stock_metrics(symbol):
    print(f"--- {symbol} ---")
    t = yf.Ticker(symbol)
    info = t.info
    print(f"Name: {info.get('longName')}")
    print(f"Price: {info.get('currentPrice', info.get('regularMarketPrice'))}")
    print(f"MCap: {info.get('marketCap')}")
    print(f"EPS: {info.get('trailingEps')}")
    print(f"BVPS: {info.get('bookValue')}")
    # Check if we have different fields for MCap
    print(f"Other fields: enterpriseValue={info.get('enterpriseValue')}")

if __name__ == "__main__":
    check_stock_metrics("2330.TW")
    check_stock_metrics("2408.TW")
    # Also check if TV-Screener data is messing up Market Explorer
    import tvscreener as tvs
    from tvscreener import StockScreener, StockField
    ss = StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    ss.search("2330")
    df = ss.get()
    if not df.empty:
        print("\n=== TVS 2330 ===")
        print(df.iloc[0].to_dict())

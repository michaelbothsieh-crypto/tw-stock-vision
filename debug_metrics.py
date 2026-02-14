import yfinance as yf
import json
import math

def check_stock_metrics(symbol):
    print(f"=== Checking Metrics for {symbol} ===")
    t = yf.Ticker(symbol)
    info = t.info
    
    price = info.get('currentPrice')
    market_cap = info.get('marketCap')
    eps = info.get('trailingEps')
    bvps = info.get('bookValue')
    
    print(f"Price: {price}")
    print(f"Market Cap: {market_cap} ({market_cap/1e12:.2f}T if TWD, {market_cap/1e9:.2f}B if US)")
    print(f"EPS: {eps}")
    print(f"BVPS: {bvps}")
    
    if eps and bvps and eps > 0 and bvps > 0:
        graham = math.sqrt(22.5 * eps * bvps)
        print(f"Calculated Graham Number: {graham:.2f}")
    else:
        print("Cannot calculate Graham Number (Missing EPS/BVPS)")

if __name__ == "__main__":
    check_stock_metrics("2330.TW")
    print("-" * 20)
    check_stock_metrics("2408.TW")

import yfinance as yf
import json
import math

def format_market_cap(val, is_tw=True):
    """格式化市值，台股用億/兆，美股用 B/T"""
    if not val or val == 0: return "-"
    try:
        if is_tw:
            if val >= 1e12:
                return f"{val/1e12:.2f} 兆"
            return f"{val/1e8:.2f} 億"
        else:
            if val >= 1e12:
                return f"{val/1e12:.2f} T"
            return f"{val/1e9:.2f} B"
    except:
        return str(val)

def check_us_metrics(symbol):
    print(f"=== Checking {symbol} ===")
    t = yf.Ticker(symbol)
    info = t.info
    
    price = info.get('currentPrice', info.get('regularMarketPrice', 0))
    raw_mcap = info.get('marketCap', 0)
    
    # Check if our detector handles US symbols correctly
    is_tw_mkt = symbol.isdigit() or symbol.endswith('.TW') or symbol.endswith('.TWO')
    formatted_mcap = format_market_cap(raw_mcap, is_tw=is_tw_mkt)
    
    eps = info.get('trailingEps', 0)
    bvps = info.get('bookValue', 0)
    
    print(f"Price: {price}")
    print(f"Raw MCap: {raw_mcap}")
    print(f"Is TW Detector: {is_tw_mkt}")
    print(f"Formatted MCap: {formatted_mcap}")
    print(f"EPS: {eps}, BVPS: {bvps}")
    
    # Financial metrics for "AI Intensity" (F-Score/Z-Score)
    net_margin = (info.get('profitMargins', 0) or 0) * 100
    roa = info.get('returnOnAssets', 0)
    f_score = 3
    if net_margin > 0: f_score += 1
    if roa > 0: f_score += 1
    
    z_score = 1.0
    if info.get('currentRatio', 0) > 1.2: z_score += 1.0
    if info.get('debtToEquity', 100) < 60: z_score += 1.0
    
    print(f"F-Score (Calculated): {f_score}")
    print(f"Z-Score (Calculated): {z_score}")

if __name__ == "__main__":
    check_us_metrics("NVDA")
    print("-" * 20)
    check_us_metrics("AAPL")

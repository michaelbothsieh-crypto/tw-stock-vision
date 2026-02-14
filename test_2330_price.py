import yfinance as yf
print(f"2330.TW: {yf.Ticker('2330.TW').info.get('currentPrice')}")
print(f"2330.HK: {yf.Ticker('2330.HK').info.get('currentPrice')}")
# Maybe 2330.TW price IS 1000+ but the info.get('currentPrice') is returning something else?
info = yf.Ticker('2330.TW').info
print(f"2330.TW all prices: current:{info.get('currentPrice')}, reg:{info.get('regularMarketPrice')}, prev:{info.get('previousClose')}")

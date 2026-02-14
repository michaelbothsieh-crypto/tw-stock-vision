import yfinance as yf
import json

def test_2330():
    print("Testing 2330.TW (TSMC)...")
    t = yf.Ticker("2330.TW")
    info = t.info
    
    interesting_keys = [
        'regularMarketPrice', 'currentPrice', 'targetMedianPrice', 'targetMeanPrice', 
        'targetLowPrice', 'targetHighPrice', 'recommendationMean', 'currency'
    ]
    
    results = {k: info.get(k) for k in interesting_keys if k in info}
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    test_2330()

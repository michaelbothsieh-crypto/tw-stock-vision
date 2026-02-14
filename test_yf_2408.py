import yfinance as yf
import json

def test_2408():
    ticker = yf.Ticker("2408.TW")
    info = ticker.info
    # 精準列印目標價相關的所有可能欄位
    target_fields = [
        'targetMeanPrice', 'targetMedianPrice', 'targetLowPrice', 'targetHighPrice',
        'numberOfAnalystOpinions', 'recommendationMean', 'recommendationKey', 'currentPrice'
    ]
    results = {f: info.get(f) for f in target_fields}
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    test_2408()

import yfinance as yf
import json

def test_methods(symbol):
    print(f"Testing {symbol}...")
    t = yf.Ticker(symbol)
    
    print("\n[INFO]")
    print(t.info)
    
    print("\n[HISTORY (1d)]")
    hist = t.history(period="1d")
    print(hist)
    if not hist.empty:
        print("Price from hist:", hist['Close'].iloc[-1])

    print("\n[BALANCESHEET]")
    try:
        bs = t.balancesheet
        print(bs.columns if hasattr(bs, 'columns') else "No columns")
    except:
        print("BS Failed")

if __name__ == "__main__":
    test_methods("1915.TWO")

import tvscreener as tvs
from tvscreener import StockScreener, StockField
import json

def diagnose():
    symbol = "2330"
    ss = StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    ss.search(symbol)
    ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE, StockField.CHANGE_PERCENT)
    df = ss.get()
    if df.empty:
        print("Tvscreener is EMPTY for 2330")
    else:
        row = df.iloc[0].to_dict()
        print("Keys in row:", list(row.keys()))
        print("Sample data:", row)

if __name__ == "__main__":
    diagnose()

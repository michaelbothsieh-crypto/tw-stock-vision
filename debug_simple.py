import tvscreener as tvs
print("Start")
ss = tvs.StockScreener()
ss.set_markets(tvs.Market.TAIWAN)
try:
    df = ss.get()
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
except Exception as e:
    print("Error:", e)
print("End")

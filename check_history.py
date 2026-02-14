import tvscreener as tvs
try:
    ss = tvs.StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    # Check if there's a way to get history. Usually screener is for current data.
    # Libraries like yfinance/tvdatafeed are for history.
    # Let's inspect available methods
    print("Methods:", dir(ss))
except Exception as e:
    print(e)

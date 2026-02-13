from tvscreener import StockScreener
import tvscreener as tvs
import json

ss = StockScreener()
ss.set_markets(tvs.Market.TAIWAN)
df = ss.get()
print("Columns available:", list(df.columns))

# Also check US
# ss_us = StockScreener()
# ss_us.set_markets(tvs.Market.AMERICA)
# df_us = ss_us.get()
# print("US Columns:", list(df_us.columns))

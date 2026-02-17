import twstock

print("--- twstock Library Demo ---")
print(f"Total stocks in codes: {len(twstock.codes)}")

# Sample a few specific stocks
examples = ['2330', '2317', '2454', '6223']
for code in examples:
    if code in twstock.codes:
        stock = twstock.codes[code]
        print(f"Code: {code}, Name: {stock.name}, Type: {stock.type}, Market: {stock.market}")
    else:
        print(f"Code: {code} not found")

# Sample an ETF just to see
if '0050' in twstock.codes:
    etf = twstock.codes['0050']
    print(f"Code: 0050, Name: {etf.name}, Type: {etf.type}")

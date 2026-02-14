from tvscreener import StockScreener, StockField
import tvscreener as tvs
import json

def test():
    ss = StockScreener()
    ss.set_markets(tvs.Market.TAIWAN)
    ss.search("2330")
    ss.select(StockField.NAME, StockField.TECHNICAL_RATING, StockField.RECOMMENDATION_MARK, StockField.PRICE_TARGET_AVERAGE)
    df = ss.get()
    if not df.empty:
        row = df.iloc[0].to_dict()
        print("\n--- 2330 Raw Data ---")
        for k, v in row.items():
            print(f"Key: [{k}], Value: [{v}]")
        
        print("\n--- Field Labels ---")
        print(f"TECHNICAL_RATING: {StockField.TECHNICAL_RATING.label}")
        print(f"RECOMMENDATION_MARK: {StockField.RECOMMENDATION_MARK.label}")
        print(f"PRICE_TARGET_AVERAGE: {StockField.PRICE_TARGET_AVERAGE.label}")

if __name__ == "__main__":
    test()

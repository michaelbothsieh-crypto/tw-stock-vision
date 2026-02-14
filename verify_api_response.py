import json
import math

class MockHandler:
    def _set_headers(self):
        pass

def test_api_output(symbol):
    print(f"Testing API Response for: {symbol}")
    handler = MockHandler()
    # 模擬 _handle_stock_lookup 的行為，直接獲取 data
    # 注意：在真實環境中 handler 是 BaseHTTPRequestHandler 的子類
    # 這裡我們手動測試關鍵邏輯
    from api.scrapers import process_tvs_row, fetch_from_yfinance
    from tvscreener import StockScreener, StockField
    import tvscreener as tvs

    is_tw = symbol.isdigit()
    ss = StockScreener()
    ss.set_markets(tvs.Market.AMERICA if not is_tw else tvs.Market.TAIWAN)
    ss.search(symbol)
    ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE, StockField.CHANGE_PERCENT, 
              StockField.VOLUME, StockField.MARKET_CAPITALIZATION, StockField.SECTOR, StockField.INDUSTRY, StockField.EXCHANGE,
              StockField.RELATIVE_VOLUME, StockField.CHAIKIN_MONEY_FLOW_20, StockField.VOLUME_WEIGHTED_AVERAGE_PRICE, 
              StockField.TECHNICAL_RATING, StockField.AVERAGE_TRUE_RANGE_14, StockField.RELATIVE_STRENGTH_INDEX_14,
              StockField.SIMPLE_MOVING_AVERAGE_50, StockField.SIMPLE_MOVING_AVERAGE_200,
              StockField.PIOTROSKI_F_SCORE_TTM, StockField.BASIC_EPS_TTM, StockField.RECOMMENDATION_MARK,
              StockField.GROSS_MARGIN_TTM, StockField.OPERATING_MARGIN_TTM, StockField.NET_MARGIN_TTM,
              StockField.ALTMAN_Z_SCORE_TTM, StockField.GRAHAM_NUMBERS_TTM, StockField.PRICE_TARGET_AVERAGE)
    df = ss.get()
    
    data = None
    if not df.empty:
        raw_row = df.iloc[0].to_dict()
        print("\nRaw Row from TVS:")
        for k, v in raw_row.items():
            filter_keys = ['Margin', 'Score', 'Graham', 'Target', 'Rating', 'Recommendation']
            if any(fk in k for fk in filter_keys):
                print(f"{k}: {v}")
        data = process_tvs_row(raw_row, symbol)
        print("TVS Data Found")
    
    if not data or data.get('fScore', 0) == 0:
        print("Triggering yfinance fallback...")
        yf_data = fetch_from_yfinance(symbol)
        if yf_data:
            if not data:
                data = yf_data
            else:
                keys_to_merge = [
                    'fScore', 'zScore', 'grahamNumber', 'eps', 'targetPrice', 'technicalRating',
                    'grossMargin', 'netMargin', 'operatingMargin', 'revGrowth', 'epsGrowth',
                    'peRatio', 'pegRatio', 'sma20', 'sma50', 'sma200', 'rsi', 'atr_p'
                ]
                for k in keys_to_merge:
                    if not data.get(k) or data.get(k) == 0:
                        val = yf_data.get(k)
                        if val is not None:
                            data[k] = val
                            print(f"Merged {k}: {val}")

    if data:
        print("\nFinal Data Keys for HealthCheck:")
        required = ['fScore', 'zScore', 'grossMargin', 'netMargin', 'operatingMargin', 'grahamNumber']
        for r in required:
            print(f"{r}: {data.get(r, 'MISSING')}")
        
        # 檢查雷達圖
        print("\nRadar Data Points:")
        for pt in data.get('radarData', []):
            print(f"{pt['subject']}: {pt['A']}")

if __name__ == "__main__":
    # 測試一個常見的台股以驗證映射與融合
    test_api_output("2330")
    print("-" * 30)
    # 測試 1915 以驗證補齊
    test_api_output("1915")

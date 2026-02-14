import json
import math
import sys
import os

# 模擬環境加入 python path
sys.path.append(os.getcwd())

from api.scrapers import process_tvs_row, fetch_from_yfinance
from tvscreener import StockScreener, StockField
import tvscreener as tvs

def verify_regression(symbol):
    print(f"\n[REGRESSION TEST] Checking {symbol}...")
    
    # 後端邏輯：如果是純數字，補 .TW / .TWO
    is_pure_digit = symbol.isdigit()
    if is_pure_digit:
        tvs_search = symbol
    else:
        tvs_search = symbol.split('.')[0]
    
    # 1. TVS 資料檢索
    is_tw = is_pure_digit or ".TW" in symbol or ".TWO" in symbol
    ss = StockScreener()
    ss.set_markets(tvs.Market.AMERICA if not is_tw else tvs.Market.TAIWAN)
    ss.search(tvs_search)
    ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE, StockField.CHANGE_PERCENT, 
              StockField.VOLUME, StockField.MARKET_CAPITALIZATION, StockField.SECTOR, StockField.INDUSTRY, StockField.EXCHANGE,
              StockField.RELATIVE_VOLUME, StockField.CHAIKIN_MONEY_FLOW_20, StockField.VOLUME_WEIGHTED_AVERAGE_PRICE, 
              StockField.TECHNICAL_RATING, StockField.AVERAGE_TRUE_RANGE_14, StockField.RELATIVE_STRENGTH_INDEX_14,
              StockField.SIMPLE_MOVING_AVERAGE_50, StockField.SIMPLE_MOVING_AVERAGE_200,
              StockField.PIOTROSKI_F_SCORE_TTM, StockField.BASIC_EPS_TTM, StockField.RECOMMENDATION_MARK,
              StockField.GROSS_MARGIN_TTM, StockField.OPERATING_MARGIN_TTM, StockField.NET_MARGIN_TTM,
              StockField.ALTMAN_Z_SCORE_TTM, StockField.GRAHAM_NUMBERS_TTM)
    
    data = None
    try:
        df = ss.get()
        if not df.empty:
            raw_row = df.iloc[0].to_dict()
            data = process_tvs_row(raw_row, symbol)
            print("✓ TVS Result obtained")
    except Exception as e:
        print(f"⚠ TVS error: {e}")

    # 2. yfinance 補強與融合
    # 邏輯：TVS 無結果，或是關鍵數據 F-Score 為空
    if not data or data.get('fScore', 0) == 0:
        print("...Fallback to yfinance")
        # 直接使用全代號或純數字
        yf_symbol = symbol 
        yf_data = fetch_from_yfinance(yf_symbol)
        
        if yf_data:
            if not data:
                data = yf_data
                print(f"✓ Obtained full data from yf for {yf_symbol}")
            else:
                # 融合邏輯
                keys_to_merge = [
                    'fScore', 'zScore', 'grahamNumber', 'eps', 'targetPrice', 'technicalRating',
                    'grossMargin', 'netMargin', 'operatingMargin'
                ]
                for k in keys_to_merge:
                    if not data.get(k) or data.get(k) == 0:
                        val = yf_data.get(k)
                        if val is not None:
                            data[k] = val
                            print(f"  + Merged {k} from yf")
    
    if not data:
        print(f"❌ REGRESSION FAILED: No data object returned for {symbol}")
        return False

    # 3. 欄位存在性檢查 (與經驗庫定義之清單對齊)
    # 財務強度 (F-Score, Z-Score) 與 葛拉漢指數 是本次修復的核心
    critical_fields = ['fScore', 'zScore', 'grahamNumber']
    missing = []
    print(f"  Final Data Check:")
    for f in critical_fields:
        val = data.get(f)
        if val is None or (isinstance(val, (int, float)) and val == 0 and f == 'grahamNumber'):
            missing.append(f)
        else:
            print(f"    ✓ {f}: {val}")
    
    if missing:
        print(f"❌ REGRESSION FAILED: Missing critical fields {missing}")
        return False
    
    print("✅ REGRESSION PASSED")
    return True

if __name__ == "__main__":
    test_symbols = ["2330", "1915"]
    results = [verify_regression(s) for s in test_symbols]
    if all(results):
        print("\n=== ALL REGRESSION TESTS PASSED ===")
        sys.exit(0)
    else:
        print("\n=== REGRESSION FAILED ===")
        sys.exit(1)

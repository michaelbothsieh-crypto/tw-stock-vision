import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import yfinance as yf
import re
from api.constants import TW_STOCK_NAMES, SECTOR_TRANSLATIONS, EXCHANGE_TRANSLATIONS

def get_field(data, keys, default=0):
    """從字典中多重金鑰尋找數值，支援 TVS 標籤與 yfinance 特性"""
    for k in keys:
        if k in data and data[k] is not None:
            val = data[k]
            # 處理 NaN (Python float('nan'))
            if isinstance(val, float) and math.isnan(val):
                continue
            # 處理 TV 的百分比字串
            if isinstance(val, str) and '%' in val:
                try: val = float(val.replace('%', ''))
                except: pass
            # 強健轉型
            try:
                res = float(val)
                # 排除某些不合理的極大值 (TVS 有時會回傳占位符)
                if res > 1e12: return default
                return res
            except (ValueError, TypeError):
                continue
    return default

def sanitize_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return obj
    return obj

def format_market_cap(val, is_tw=True):
    """格式化市值，台股用億/兆，美股用 B/T"""
    if not val or val == 0: return "-"
    try:
        if is_tw:
            if val >= 1e12:
                return f"{val/1e12:.2f} 兆"
            return f"{val/1e8:.2f} 億"
        else:
            if val >= 1e12:
                return f"{val/1e12:.2f} T"
            return f"{val/1e9:.2f} B"
    except:
        return str(val)

def fetch_from_yfinance(symbol):
    try:
        ticker_symbol = symbol
        info = None
        if symbol.isdigit():
            # TW stocks - Try .TW first, then .TWO
            for suffix in [".TW", ".TWO"]:
                test_ticker = symbol + suffix
                t = yf.Ticker(test_ticker)
                try:
                    info = t.info
                    # Check if we got meaningful data
                    if info and ('regularMarketPrice' in info or 'currentPrice' in info or 'longName' in info):
                        ticker_symbol = test_ticker
                        break
                    else:
                        # Backup: Try history if info is 404
                        hist = t.history(period="1d")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            return {
                                "symbol": symbol,
                                "name": TW_STOCK_NAMES.get(symbol, f"台股 {symbol}"),
                                "price": price,
                                "change": 0,
                                "changePercent": 0,
                                "volume": 0,
                                "marketCap": 0,
                                "technicalRating": 0.5,
                                "analystRating": 3,
                                "targetPrice": price * 1.1,
                                "sma50": price,
                                "sma200": price,
                                "sector": "-",
                                "industry": "-",
                                "exchange": suffix[1:],
                                "fScore": 5,
                                "zScore": 1.5,
                                "grossMargin": 0,
                                "netMargin": 0,
                                "operatingMargin": 0,
                                "eps": 0,
                                "grahamNumber": price * 0.9,
                                "source": "yf-hist"
                            }
                except:
                    continue
        else:
            t = yf.Ticker(ticker_symbol)
            info = t.info

        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info and 'longName' not in info):
            return None
            
        # 強化指標抓取
        price = info.get('regularMarketPrice', info.get('currentPrice', info.get('previousClose', info.get('ask', 0))))
        prev_close = info.get('regularMarketPreviousClose', info.get('previousClose', price))
        change_p = ((price - prev_close) / prev_close * 100) if prev_close else 0
        
        # 財務指標
        gross_margin = (info.get('grossMargins', 0) or 0) * 100
        net_margin = (info.get('profitMargins', 0) or 0) * 100
        operating_margin = (info.get('operatingMargins', 0) or 0) * 100
        eps = info.get('trailingEps', info.get('forwardEps', info.get('epsTrailingTwelveMonths', 0))) or 0
        bvps = info.get('bookValue', 0) or 0
        
        # 市值處理
        raw_mcap = info.get('marketCap', 0)
        # 精確判定：純數字或帶有特定尾碼視為台股
        is_tw_mkt = bool(re.match(r'^\d+$', symbol)) or symbol.endswith('.TW') or symbol.endswith('.TWO')
        formatted_mcap = format_market_cap(raw_mcap, is_tw=is_tw_mkt)

        # 目標價：精準映射 yfinance 的多個可能欄位
        target_price = info.get('targetMedianPrice', info.get('targetMeanPrice', info.get('targetLowPrice', price * 1.1)))

        # F-Score 邏輯加強
        f_score = 3
        if net_margin > 0: f_score += 1
        if info.get('returnOnAssets', 0) > 0: f_score += 1
        if info.get('operatingCashflow', 0) > 0: f_score += 1
        if info.get('returnOnEquity', 0) > 10: f_score += 1
        if info.get('revenueGrowth', 0) > 0: f_score += 1

        z_score = 1.0
        if info.get('currentRatio', 0) > 1.2: z_score += 1.0
        if info.get('debtToEquity', 100) < 60: z_score += 1.0
        
        # 合理價 (Graham) 退卻邏輯：若 EPS 異常，則採用類似 P/B 的估值
        graham = 0
        if eps > 0 and bvps > 0:
            graham = math.sqrt(22.5 * eps * bvps)
        else:
            # 退卻：採用淨值估法 (假設最低 1.2 倍淨值)
            graham = bvps * 1.5 if bvps > 0 else (price * 0.8)

        return {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', symbol)),
            "price": price,
            "changePercent": change_p,
            "marketCap": formatted_mcap,
            "technicalRating": 0.5 if price > info.get('fiftyDayAverage', price) else -0.5,
            "analystRating": info.get('recommendationMean', 3),
            "targetPrice": target_price,
            "sma50": info.get('fiftyDayAverage', price),
            "sma200": info.get('twoHundredDayAverage', price),
            "fScore": min(9, f_score),
            "zScore": round(z_score, 2),
            "grahamNumber": round(graham, 2),
            "eps": eps,
            "source": "yfinance"
        }
    except Exception as e:
        print(f"yfinance error: {e}")
        return None
    except Exception as e:
        print(f"yfinance error: {e}")
        return None
    except Exception as e:
        print(f"yfinance error: {e}")
        return None

def process_tvs_row(row, symbol):
    """將 tvscreener 的 row 轉換為標準化的資料格式"""
    price = get_field(row, ['Price'], 0)
    eps = get_field(row, ['Basic EPS (TTM)', 'EPS Diluted (TTM)'], 0)
    
    # 評級邏輯: TV 可能返回字串 like 'Strong Buy'
    # 指標轉換與補全
    atr = get_field(row, ['Average True Range (14)', StockField.AVERAGE_TRUE_RANGE_14.label], 0)
    atr_p = (atr / price * 100) if price > 0 else 0

    # 評級邏輯：優先使用數值型，否則回退到字串轉換
    tech_rating = get_field(row, ['Technical Rating', StockField.TECHNICAL_RATING.label], None)
    if tech_rating is None:
        rec = row.get('Recommendation', 'Neutral')
        tech_rating = 0
        if isinstance(rec, str):
            if 'Strong Buy' in rec: tech_rating = 1
            elif 'Buy' in rec: tech_rating = 0.5
            elif 'Strong Sell' in rec: tech_rating = -1
            elif 'Sell' in rec: tech_rating = -0.5

    # 優先嘗試從常數表獲取中文名稱 (針對台股)
    display_name = row.get('Description', row.get('Name', symbol))
    raw_mcap = get_field(row, ['Market Capitalization'], 0)
    is_tw = bool(re.match(r'^\d+$', symbol))
    formatted_mcap = format_market_cap(raw_mcap, is_tw=is_tw)

    data = {
        "symbol": symbol,
        "name": display_name,
        "price": price,
        "change": get_field(row, ['Change'], 0),
        "changePercent": get_field(row, ['Change %'], 0),
        "volume": get_field(row, ['Volume'], 0),
        "marketCap": formatted_mcap,
        "technicalRating": tech_rating,
        "analystRating": get_field(row, ['Analyst Rating', StockField.RECOMMENDATION_MARK.label], 3),
        "targetPrice": get_field(row, ['Target Price (Average)', 'Price Target Mean', StockField.PRICE_TARGET_AVERAGE.label], 0),
        "sma50": get_field(row, ['Simple Moving Average (50)'], price),
        "sma200": get_field(row, ['Simple Moving Average (200)'], price),
        "rsi": get_field(row, ['Relative Strength Index (14)'], 50),
        "rvol": get_field(row, ['Relative Volume'], 1),
        "cmf": get_field(row, ['Chaikin Money Flow (20)'], 0),
        "atr": atr,
        "atr_p": atr_p,
        "vwap": get_field(row, ['Volume Weighted Average Price'], price),
        "fScore": get_field(row, ['Piotroski F-Score (TTM)', 'Piotroski F-Score', StockField.PIOTROSKI_F_SCORE_TTM.label], 0),
        "grossMargin": get_field(row, ['Gross Margin (TTM)', 'Gross Margin', StockField.GROSS_MARGIN_TTM.label], 0),
        "netMargin": get_field(row, ['Net Margin (TTM)', 'Net Margin', StockField.NET_MARGIN_TTM.label], 0),
        "operatingMargin": get_field(row, ['Operating Margin (TTM)', 'Operating Margin', StockField.OPERATING_MARGIN_TTM.label], 0),
        "zScore": get_field(row, ['Altman Z-Score (TTM)', 'Altman Z-Score', StockField.ALTMAN_Z_SCORE_TTM.label], 0),
        "eps": eps,
        "roe": get_field(row, ['Return on Equity (TTM)', 'Return on Equity % (MRQ)', 'RETURN_ON_EQUITY_TTM'], 0),
        "roa": get_field(row, ['Return on Assets (TTM)', 'Return on Assets % (MRQ)', 'RETURN_ON_ASSETS_TTM'], 0),
        "debtToEquity": get_field(row, ['Debt to Equity Ratio (MRQ)', 'Debt to Equity FQ', 'DEBT_TO_EQUITY_RATIO_MRQ'], 0),
        "revGrowth": get_field(row, ['Revenue (TTM YoY Growth)', 'Revenue (Annual YoY Growth)', 'REVENUE_TTM_YOY_GROWTH'], 0),
        "netGrowth": get_field(row, ['Net Income (TTM YoY Growth)', 'Net Income (Annual YoY Growth)', 'NET_INCOME_TTM_YOY_GROWTH'], 0),
        "yield": get_field(row, ['Dividend Yield Forward', 'Dividend Yield Recent', 'DIVIDEND_YIELD_RECENT'], 0),
        "sector": row.get('Sector', '-'),
        "industry": row.get('Industry', '-'),
        "exchange": row.get('Exchange', '-'),
        "source": "tvscreener"
    }
    
    # 補全葛拉漢數
    if eps > 0:
        ma_calc = math.sqrt(max(0, 22.5 * eps * (price / 1.5)))
        data["grahamNumber"] = get_field(row, ["Graham's Number (TTM)", "Graham's Number (FY)", "Graham's Number"], ma_calc)
    else:
        data["grahamNumber"] = get_field(row, ["Graham's Number (TTM)", "Graham's Number (FY)", "Graham's Number"], 0)
        
    return data

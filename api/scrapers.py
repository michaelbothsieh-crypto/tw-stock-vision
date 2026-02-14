import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import yfinance as yf
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
            
        price = info.get('regularMarketPrice', info.get('currentPrice', info.get('previousClose', 0)))
        prev_close = info.get('regularMarketPreviousClose', info.get('previousClose', price))
        change = price - prev_close
        change_p = (change / prev_close * 100) if prev_close else 0
        
        sma50 = info.get('fiftyDayAverage', price)
        sma200 = info.get('twoHundredDayAverage', price)
        momentum = 0.5 if price > sma50 else -0.5
        
        gross_margin = (info.get('grossMargins', 0) or 0) * 100
        net_margin = (info.get('profitMargins', 0) or 0) * 100
        operating_margin = (info.get('operatingMargins', 0) or 0) * 100

        eps = info.get('trailingEps', info.get('forwardEps', info.get('epsTrailingTwelveMonths', 0))) or 0
        bvps = info.get('bookValue', 0) or 0
        
        graham_number = math.sqrt(max(0, 22.5 * eps * bvps)) if eps > 0 and bvps > 0 else (price * 0.85)

        f_score_est = 3
        if net_margin > 0: f_score_est += 2
        if info.get('returnOnAssets', 0) > 0: f_score_est += 2
        if info.get('operatingCashflow', 0) > 0: f_score_est += 2

        z_score_est = 1.0 + (0.5 if info.get('currentRatio', 0) > 1.5 else 0) + (1.0 if info.get('debtToEquity', 100) < 50 else 0)
        
        return {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', symbol)),
            "price": price,
            "changePercent": change_p,
            "technicalRating": momentum,
            "analystRating": info.get('recommendationMean', 3),
            "targetPrice": info.get('targetMedianPrice', info.get('targetMeanPrice', price * 1.1)),
            "sma50": sma50,
            "sma200": sma200,
            "fScore": min(9, f_score_est),
            "zScore": round(z_score_est, 2),
            "grahamNumber": round(graham_number, 2),
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

    data = {
        "symbol": symbol,
        "name": row.get('Description', row.get('Name', symbol)),
        "price": price,
        "change": get_field(row, ['Change'], 0),
        "changePercent": get_field(row, ['Change %'], 0),
        "volume": get_field(row, ['Volume'], 0),
        "marketCap": get_field(row, ['Market Capitalization'], 0),
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

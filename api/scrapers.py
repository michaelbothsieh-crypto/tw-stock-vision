import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import yfinance as yf
from api.constants import TW_STOCK_NAMES, SECTOR_TRANSLATIONS, EXCHANGE_TRANSLATIONS

def get_field(data, keys, default=0):
    for k in keys:
        if k in data and data[k] is not None:
            val = data[k]
            if isinstance(val, str) and '%' in val:
                try: val = float(val.replace('%', ''))
                except: pass
            return val
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
        if symbol.isdigit():
            test_ticker = symbol + ".TW"
            t = yf.Ticker(test_ticker)
            info = t.info
            if info and 'regularMarketPrice' in info:
                ticker_symbol = test_ticker
            else:
                test_ticker = symbol + ".TWO"
                t = yf.Ticker(test_ticker)
                info = t.info
                if info and 'regularMarketPrice' in info:
                    ticker_symbol = test_ticker
        else:
            t = yf.Ticker(ticker_symbol)
            info = t.info

        if not info or 'regularMarketPrice' not in info:
            return None
            
        price = info.get('regularMarketPrice', 0)
        prev_close = info.get('regularMarketPreviousClose', price)
        change = price - prev_close
        change_p = (change / prev_close * 100) if prev_close else 0
        
        sma50 = info.get('fiftyDayAverage', price)
        sma200 = info.get('twoHundredDayAverage', price)
        momentum = 0.5 if price > sma50 else -0.5
        
        gross_margin = info.get('grossMargins', 0)
        net_margin = info.get('profitMargins', 0)
        operating_margin = info.get('operatingMargins', 0)
        
        if gross_margin: gross_margin *= 100
        if net_margin: net_margin *= 100
        if operating_margin: operating_margin *= 100

        eps = info.get('trailingEps', info.get('forwardEps', 0))
        bvps = info.get('bookValue', 0)
        
        graham_number = 0
        if eps > 0 and bvps > 0:
            graham_number = math.sqrt(max(0, 22.5 * eps * bvps))
        elif eps > 0:
            graham_number = math.sqrt(max(0, 22.5 * eps * (price / 1.5)))
        
        return {
            "symbol": symbol,
            "name": info.get('longName', symbol),
            "price": price,
            "change": change,
            "changePercent": change_p,
            "volume": info.get('regularMarketVolume', 0),
            "marketCap": info.get('marketCap', 0),
            "technicalRating": momentum,
            "analystRating": info.get('recommendationMean', 3),
            "targetPrice": info.get('targetMedianPrice', info.get('targetMeanPrice', 0)),
            "sma50": sma50,
            "sma200": sma200,
            "sector": info.get('sector', '-'),
            "industry": info.get('industry', '-'),
            "exchange": info.get('exchange', 'TWSE'),
            "fScore": 4 + (1 if net_margin > 0 else 0),
            "zScore": (gross_margin / 20) if gross_margin else 1.5,
            "grossMargin": gross_margin,
            "netMargin": net_margin,
            "operatingMargin": operating_margin,
            "eps": eps,
            "grahamNumber": graham_number,
            "source": "yfinance"
        }
    except Exception as e:
        print(f"yfinance error: {e}")
        return None

def process_tvs_row(row, symbol):
    """將 tvscreener 的 row 轉換為標準化的資料格式"""
    price = get_field(row, ['Price'], 0)
    eps = get_field(row, ['Basic EPS (TTM)', 'EPS Diluted (TTM)'], 0)
    
    # 評級邏輯: TV 可能返回字串 like 'Strong Buy'
    rec = row.get('Recommendation', 'Neutral')
    tech_score = 0
    if 'Strong Buy' in rec: tech_score = 1
    elif 'Buy' in rec: tech_score = 0.5
    elif 'Strong Sell' in rec: tech_score = -1
    elif 'Sell' in rec: tech_score = -0.5

    # 指標轉換與補全
    atr = get_field(row, ['Average True Range (14)'], 0)
    atr_p = (atr / price * 100) if price > 0 else 0

    data = {
        "symbol": symbol,
        "name": row.get('Description', row.get('Name', symbol)),
        "price": price,
        "change": get_field(row, ['Change'], 0),
        "changePercent": get_field(row, ['Change %'], 0),
        "volume": get_field(row, ['Volume'], 0),
        "marketCap": get_field(row, ['Market Capitalization'], 0),
        "technicalRating": tech_score,
        "targetPrice": get_field(row, ['Price Target Mean', 'Price Target Median'], 0),
        "sma50": get_field(row, ['Simple Moving Average (50)'], price),
        "sma200": get_field(row, ['Simple Moving Average (200)'], price),
        "rsi": get_field(row, ['Relative Strength Index (14)'], 50),
        "rvol": get_field(row, ['Relative Volume'], 1),
        "cmf": get_field(row, ['Chaikin Money Flow (20)'], 0),
        "atr": atr,
        "atr_p": atr_p,
        "vwap": get_field(row, ['Volume Weighted Average Price'], price),
        "fScore": get_field(row, ['Piotroski F-Score (TTM)'], 0),
        "eps": eps,
        "sector": row.get('Sector', '-'),
        "industry": row.get('Industry', '-'),
        "exchange": row.get('Exchange', '-'),
        "source": "tvscreener"
    }
    
    # 補全葛拉漢數
    if eps > 0:
        ma_calc = math.sqrt(max(0, 22.5 * eps * (price / 1.5)))
        data["grahamNumber"] = get_field(row, ["Graham's Number"], ma_calc)
    else:
        data["grahamNumber"] = 0
        
    return data

import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import yfinance as yf
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from api.constants import TW_STOCK_NAMES, SECTOR_TRANSLATIONS, EXCHANGE_TRANSLATIONS
from api.db import get_db_connection, return_db_connection

def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    # ✅ 安全修復：預設啟用 SSL 驗證，僅在明確設定環境變數時才停用（用於本地開發除錯）
    if os.environ.get('DISABLE_SSL_VERIFY', '').lower() == 'true':
        session.verify = False
        print("[Security] WARNING: SSL verification disabled via DISABLE_SSL_VERIFY env var")
    return session


def get_stock_name(symbol, default=None):
    """
    Get stock name from memory constant or DB.
    """
    # 1. Try memory first
    if symbol in TW_STOCK_NAMES:
        return TW_STOCK_NAMES[symbol]
    
    # 2. Try DB
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM stock_names WHERE symbol = %s", (symbol,))
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
        except Exception as e:
            print(f"[scrapers] get_stock_name DB error for {symbol}: {e}")
        finally:
            return_db_connection(conn)
    
    return default or symbol



def trunc2(value):
    """Truncate to 2 decimals without rounding (finance style)."""
    try:
        v = float(value)
        return math.trunc(v * 100) / 100
    except (TypeError, ValueError):
        return 0

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
        # 強制台股代號 (4位數字) 加上 .TW 後綴，確保抓取精確度
        yf_symbol = symbol
        if re.match(r'^\d{4,6}$', symbol):
            yf_symbol = f"{symbol}.TW"
        
        # 如果 symbol 已經有 .TW/.TWO 則保留
        elif re.search(r'\.TW[O]?$', symbol, re.IGNORECASE):
            yf_symbol = symbol.upper()

        ticker_symbol = yf_symbol
        ticker = yf.Ticker(yf_symbol)
        # 設置超時限制，避免外部 API 阻塞主線程
        info = ticker.get_info(proxy=None, timeout=10)

        # If initial fetch with yf_symbol (potentially .TW added) failed, and original symbol was a digit,
        # try the original .TW/.TWO fallback logic.
        if (not info or ('regularMarketPrice' not in info and 'currentPrice' not in info and 'longName' not in info)) and symbol.isdigit():
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
                                "name": get_stock_name(symbol, f"台股 {symbol}"),
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
                except Exception as e:
                    print(f"[scrapers] Fuzzy search error for {symbol}: {e}")
                    continue
        else:
            t = yf.Ticker(ticker_symbol)
            info = t.get_info(proxy=None, timeout=10)

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
        
        # 獲利指標單一化 (*100)
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        roa = (info.get('returnOnAssets', 0) or 0) * 100
        rev_growth = (info.get('revenueGrowth', 0) or 0) * 100
        debt_ratio = (info.get('debtToEquity', 0) or 0) # yf 的 debtToEquity 通常已經是 100 基準，如 18.18
        
        # 市值處理
        raw_mcap = info.get('marketCap', 0)
        is_tw_mkt = bool(re.match(r'^\d{4,6}$', symbol)) or symbol.endswith('.TW') or symbol.endswith('.TWO')
        formatted_mcap = format_market_cap(raw_mcap, is_tw=is_tw_mkt)

        # 目標價
        target_price = info.get('targetMedianPrice', info.get('targetMeanPrice', info.get('targetLowPrice', price * 1.1)))

        # F-Score 邏輯加強
        f_score = 3
        if net_margin > 0: f_score += 1
        if roa > 0: f_score += 1
        if info.get('operatingCashflow', 0) > 0: f_score += 1
        if roe > 10: f_score += 1
        if rev_growth > 0: f_score += 1

        z_score = 1.0
        if info.get('currentRatio', 0) > 1.2: z_score += 1.0
        if debt_ratio < 60: z_score += 1.0
        
        # 估值邏輯
        graham = 0
        if eps > 0 and bvps > 0:
            graham = math.sqrt(22.5 * eps * bvps)

        return {
            "symbol": symbol,
            "name": get_stock_name(symbol, info.get('longName', symbol)),
            "price": price,
            "changePercent": trunc2(change_p),
            "volume": info.get('regularMarketVolume', info.get('volume', 0)),
            "marketCap": formatted_mcap,
            "grossMargin": trunc2(gross_margin),
            "netMargin": trunc2(net_margin),
            "operatingMargin": trunc2(operating_margin),
            "eps": eps,
            "roe": trunc2(roe),
            "roa": trunc2(roa),
            "debtToEquity": trunc2(debt_ratio),
            "revGrowth": trunc2(rev_growth),
            "technicalRating": 0.5 if price > info.get('fiftyDayAverage', price) else -0.5,
            "analystRating": info.get('recommendationMean', 3),
            "targetPrice": target_price,
            "sma50": info.get('fiftyDayAverage', price),
            "sma200": info.get('twoHundredDayAverage', price),
            "fScore": min(9, f_score),
            "zScore": trunc2(z_score),
            "grahamNumber": trunc2(graham),
            "source": "yfinance"
        }
    except Exception as e:
        print(f"yfinance error: {e}")
        return None

def fetch_history_from_yfinance(symbol, period="1y", interval="1d", max_points=365):
    """Fetch OHLCV history for charting from yfinance."""
    normalized = symbol.strip().upper()
    candidates = []

    # Strategy: Try specific suffixes based on format
    if re.match(r'^\d{4,6}$', normalized):
        candidates = [f"{normalized}.TW", f"{normalized}.TWO"]
    elif re.search(r'\.TW[O]?$', normalized, re.IGNORECASE):
        candidates = [normalized]
    else:
        # US or other
        candidates = [normalized]

    for ticker_symbol in candidates:
        try:
            # print(f"DEBUG: Fetching history for {ticker_symbol}...")
            ticker = yf.Ticker(ticker_symbol)
            # [ 性能優化 ] 設置超時限制或重試限制
            # yfinance 內部可能阻塞，我們確保僅獲取必要的數據點
            hist = ticker.history(period=period, interval=interval, auto_adjust=True, timeout=5)
            
            if hist is None or hist.empty:
                continue

            hist = hist.reset_index()
            # Handle different index names (Date vs Datetime)
            time_col = None
            for col in ["Date", "Datetime"]:
                if col in hist.columns:
                    time_col = col
                    break
            
            if not time_col:
                continue

            # Convert to list of dicts
            output = []
            # Take only needed columns
            needed_cols = ["Open", "High", "Low", "Close", "Volume"]
            
            # Ensure columns exist
            if not all(col in hist.columns for col in needed_cols):
                 continue

            rows = hist.tail(max_points).to_dict(orient="records")
            is_intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]
            
            for r in rows:
                try:
                    ts = r[time_col]
                    if is_intraday:
                        if hasattr(ts, "strftime"):
                            # 分時數據顯示時間即可
                            date_str = ts.strftime("%H:%M")
                        else:
                            # Fallback: manually stringify and extract time if strftime missing
                            s = str(ts)
                            # Expecting "YYYY-MM-DD HH:MM:SS"
                            if ' ' in s:
                                date_str = s.split(' ')[1][:5]
                            else:
                                date_str = s
                    else:
                        date_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts).split(' ')[0]
                    
                    record = {
                        "Date": date_str,
                        "Open": float(r["Open"] or 0),
                        "High": float(r["High"] or 0),
                        "Low": float(r["Low"] or 0),
                        "Close": float(r["Close"] or 0),
                        "Volume": float(r["Volume"] or 0)
                    }
                    
                    if record["Close"] > 0:
                        output.append(record)
                except Exception:
                    continue

            if output:
                return output
                
        except Exception:
            continue

    return []

def calculate_rsi(history, period=14):
    """Calculate RSI from OHLCV history list of dicts."""
    if not history or len(history) < period + 1:
        return 50.0
    
    closes = [h['Close'] for h in history]
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))
    
    # Simple average for the first period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # Smoothing for the rest
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

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
        "name": get_stock_name(symbol, display_name),
        "price": price,
        "change": get_field(row, ['Change'], 0),
        "changePercent": trunc2(get_field(row, ['Change %'], 0)),
        "volume": get_field(row, ['Volume'], 0),
        "avgVolume": get_field(row, ['Average Volume (10 day)', 'Average Volume (30 day)', StockField.AVERAGE_VOLUME_30_DAY.label], 0),
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
        "fScore": get_field(row, ['Piotroski F-Score (TTM)', 'Piotroski F-Score', 'Piotroski F‑Score', StockField.PIOTROSKI_F_SCORE_TTM.label], 0),
        "grossMargin": get_field(row, ['Gross Margin (TTM)', 'Gross Margin', 'Gross Margin %', StockField.GROSS_MARGIN_TTM.label], 0),
        "netMargin": get_field(row, ['Net Margin (TTM)', 'Net Margin', 'Profit Margin', StockField.NET_MARGIN_TTM.label], 0),
        "operatingMargin": get_field(row, ['Operating Margin (TTM)', 'Operating Margin', StockField.OPERATING_MARGIN_TTM.label], 0),
        "zScore": get_field(row, ['Altman Z-Score (TTM)', 'Altman Z-Score', 'Altman Z‑Score', StockField.ALTMAN_Z_SCORE_TTM.label], 0),
        "eps": eps,
        "epsGrowth": get_field(row, ['EPS Diluted (TTM YoY Growth)', StockField.EPS_DILUTED_TTM_YOY_GROWTH.label], 0),
        "peRatio": get_field(row, ['Price to Earnings Ratio (TTM)', StockField.PRICE_TO_EARNINGS_RATIO_TTM.label], 0),
        "pbRatio": get_field(row, ['Price to Book (MRQ)', StockField.PRICE_TO_BOOK_MRQ.label], 0),
        "currentRatio": get_field(row, ['Current Ratio (MRQ)', StockField.CURRENT_RATIO_MRQ.label], 0),
        "quickRatio": get_field(row, ['Quick Ratio (MRQ)', StockField.QUICK_RATIO_MRQ.label], 0),
        "freeCashFlow": get_field(row, ['Free Cash Flow (TTM)', StockField.FREE_CASH_FLOW_TTM.label], 0),
        "roe": get_field(row, ['Return on Equity (TTM)', 'Return on Equity % (MRQ)', 'Return on Equity', 'RETURN_ON_EQUITY_TTM', 'Return on assets (TTM)'], 0),
        "roa": get_field(row, ['Return on Assets (TTM)', 'Return on Assets % (MRQ)', 'Return on Assets', 'RETURN_ON_ASSETS_TTM'], 0),
        "debtToEquity": get_field(row, ['Debt to Equity Ratio (MRQ)', 'Total debt over total equity (MRQ)', 'Debt to Equity Ratio', 'Debt to Equity FQ', 'DEBT_TO_EQUITY_RATIO_MRQ'], 0),
        "revGrowth": get_field(row, ['Revenue (TTM YoY Growth)', 'Revenue growth (TTM YoY)', 'Revenue (Annual YoY Growth)', 'REVENUE_TTM_YOY_GROWTH'], 0),
        "netGrowth": get_field(row, ['Net Income (TTM YoY Growth)', 'Net income growth (TTM YoY)', 'Net Income (Annual YoY Growth)', 'NET_INCOME_TTM_YOY_GROWTH'], 0),
        "yield": get_field(row, ['Dividend Yield Forward', 'Dividend Yield Recent', 'DIVIDEND_YIELD_RECENT', 'Dividends Yield Recent', 'Dividend yield - recent'], 0),
        "volatility": get_field(row, ['Volatility'], 0),
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

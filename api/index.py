from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import re
import os
import time
import yfinance as yf
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Simple mapping for popular TW stocks to Chinese names
# Simple mapping for popular TW stocks to Chinese names
TW_STOCK_NAMES = {
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2303": "聯電", "2308": "台達電",
    "2412": "中華電", "2881": "富邦金", "2882": "國泰金", "2886": "兆豐金", "2891": "中信金",
    "1301": "台塑", "1303": "南亞", "1326": "台化", "6505": "台塑化", "2002": "中鋼",
    "2603": "長榮", "2609": "陽明", "2615": "萬海", "3008": "大立光", "3711": "日月光投控",
    "2884": "玉山金", "5880": "合庫金", "2892": "第一金", "2885": "元大金", "2880": "華南金",
    "2883": "開發金", "2887": "台新金", "2890": "永豐金", "3231": "緯創", "2382": "廣達",
    "2357": "華碩", "2356": "英業達", "2353": "宏碁", "2409": "友達", "3481": "群創",
    "3045": "台灣大", "4904": "遠傳", "2912": "統一超", "1216": "統一", "1101": "台泥",
    "1102": "亞泥", "2395": "研華", "2301": "光寶科", "2345": "智邦", "2379": "瑞昱",
    "3034": "聯詠", "3037": "欣興", "2327": "國巨", "2474": "可成", "4938": "和碩",
    "9910": "豐泰", "9921": "巨大", "5871": "中租-KY", "5876": "上海商銀", "2801": "彰銀",
    "2834": "臺企銀", "2324": "仁寶", "2354": "鴻準", "2492": "華新科", "2376": "技嘉",
    "2377": "微星", "2313": "華通", "3017": "奇鋐", "3035": "智原", "3529": "力旺",
    "3661": "世芯-KY", "6669": "緯穎", "6415": "矽力*-KY", "6770": "力積電", "6515": "穎崴",
    "2207": "和泰車", "2201": "裕隆", "2610": "華航", "2618": "長榮航", "2723": "美食-KY",
    "2727": "王品", "2707": "晶華", "9904": "寶成", "9914": "美利達", "1504": "東元",
    "1513": "中興電", "1519": "華城", "1605": "華新", "1907": "永豐餘",
    "2344": "華邦電", "2408": "南亞科", "3035": "智原", "2337": "旺宏", "2363": "矽統"
}

db_pool = None
db_alive = True
db_fail_count = 0

def get_db_connection():
    global db_pool, db_alive, db_fail_count
    if not db_alive:
        return None
    
    if not db_pool:
        try:
            from psycopg2 import pool
            db_pool = pool.ThreadedConnectionPool(
                1, 10,
                os.environ['DATABASE_URL'],
                sslmode='require',
                connect_timeout=2
            )
            print("Database connection pool created.")
            db_fail_count = 0
        except Exception as e:
            db_fail_count += 1
            print(f"Error creating connection pool ({db_fail_count}): {e}")
            if db_fail_count > 2:
                print("Disabling DB attempts (Circuit Breaker).")
                db_alive = False
            try:
                return psycopg2.connect(os.environ['DATABASE_URL'], connect_timeout=2)
            except Exception as e2:
                return None
    
    try:
        conn = db_pool.getconn()
        db_fail_count = 0
        return conn
    except Exception as e:
        db_fail_count += 1
        if db_fail_count > 5:
            db_alive = False
        return None

def return_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)
    elif conn:
        conn.close()

def init_db():
    try:
        conn = get_db_connection()
        if not conn:
            print("Skipping DB Init: Database unreachable.")
            return
        try:
            cur = conn.cursor()
            # Stock Cache Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_cache (
                    symbol TEXT PRIMARY KEY,
                    data JSONB,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Users Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nickname TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Portfolio Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_items (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    symbol TEXT NOT NULL,
                    entry_price NUMERIC NOT NULL,
                    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
        finally:
            return_db_connection(conn)
    except Exception as e:
        print(f"init_db failed: {e}")

def fetch_from_yfinance(symbol):
    """Fallback to yfinance for stock data"""
    try:
        # Normalize symbol for TW
        ticker_symbol = symbol
        if symbol.isdigit():
            # Try TW then TWO
            for suffix in [".TW", ".TWO"]:
                test_ticker = symbol + suffix
                t = yf.Ticker(test_ticker)
                if t.info and 'regularMarketPrice' in t.info:
                    ticker_symbol = test_ticker
                    break
        
        t = yf.Ticker(ticker_symbol)
        info = t.info
        if not info or 'regularMarketPrice' not in info:
            return None
            
        print(f"yfinance found data for: {ticker_symbol}")
        
        # Map to our structure
        price = info.get('regularMarketPrice', 0)
        prev_close = info.get('regularMarketPreviousClose', price)
        change = price - prev_close
        change_p = (change / prev_close * 100) if prev_close else 0
        
        # Radar/SMC Scores (Mocked from yfinance data)
        # 1. Momentum proxy: 50d SMA vs 200d SMA
        sma50 = info.get('fiftyDayAverage', 0)
        sma200 = info.get('twoHundredDayAverage', 0)
        momentum = 70 if price > sma50 > sma200 else 50
        
        data = {
            "symbol": symbol,
            "name": info.get('longName', symbol),
            "price": price,
            "change": change,
            "changePercent": change_p,
            "volume": info.get('regularMarketVolume', 0),
            "marketCap": info.get('marketCap', 0),
            "rvol": 1.0, # N/A in basic yf
            "cmf": 0,
            "vwap": price,
            "technicalRating": 0.5 if price > sma50 else 0,
            "analystRating": info.get('recommendationMean', 3),
            "targetPrice": info.get('targetMedianPrice', info.get('targetMeanPrice', 0)),
            "rsi": 50,
            "atr_p": 2.0,
            "sma20": info.get('fiftyDayAverage', 0), # Best we have easily
            "sma50": sma50,
            "sma200": sma200,
            "perf_w": 0,
            "perf_m": 0,
            "perf_ytd": 0,
            "volatility": 0,
            "smcScore": 60 if price > sma50 else 40,
            "prediction": {
                 "confidence": "中 (yf fallback)",
                 "upper": price * 1.05,
                 "lower": price * 0.95,
                 "days": 3
            },
            "radarData": [
                {"subject": "動能 (Momentum)", "A": momentum, "fullMark": 100},
                {"subject": "價值 (Value)", "A": 60, "fullMark": 100},
                {"subject": "安全性 (Safety)", "A": 70, "fullMark": 100},
                {"subject": "趨勢 (Trend)", "A": 65, "fullMark": 100},
                {"subject": "關注 (Attention)", "A": 50, "fullMark": 100},
            ],
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "updatedAt": "yfinance fallback",
            "source": "yfinance"
        }
        return data
    except Exception as e:
        print(f"yfinance error: {e}")
        return None

# Initialize DB on start (Note: In pure serverless like Vercel, this might run on every cold start)
# try:
#     init_db()
# except Exception as e:
#     print(f"DB Init Error: {e}")

class handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            action = data.get('action')
            conn = get_db_connection()
            cur = conn.cursor()

            if action == 'register_user':
                nickname = data.get('nickname')
                user_id = data.get('id')
                if not nickname or not user_id:
                    self.wfile.write(json.dumps({"error": "Missing nickname or id"}).encode('utf-8'))
                    return
                
                print(f"Registering user: {nickname} ({user_id})")
                try:
                    # Check if ID exists, if so update nickname, else insert
                    cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    if cur.fetchone():
                        cur.execute("UPDATE users SET nickname = %s, created_at = NOW() WHERE id = %s", (nickname, user_id))
                    else:
                        cur.execute("INSERT INTO users (id, nickname) VALUES (%s, %s)", (user_id, nickname))
                    conn.commit()
                    self.wfile.write(json.dumps({"status": "success", "user": {"id": user_id, "nickname": nickname}}).encode('utf-8'))
                except Exception as e:
                    conn.rollback()
                    print(f"DB Error during registration: {e}")
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

            elif action == 'add_portfolio':
                user_id = data.get('user_id')
                symbol = data.get('symbol')
                price = data.get('price')
                
                print(f"Adding to portfolio: {user_id} - {symbol} @ {price}")
                
                try:
                    cur.execute("""
                        INSERT INTO portfolio_items (user_id, symbol, entry_price, entry_date)
                        VALUES (%s, %s, %s, NOW())
                        RETURNING id
                    """, (user_id, symbol, price))
                    conn.commit()
                    self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
                except Exception as e:
                    conn.rollback()
                    print(f"DB Error adding portfolio: {e}")
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            
            # Fetch user portfolio
            elif action == 'get_portfolio':
                user_id = data.get('user_id')
                cur.execute("""
                    SELECT p.symbol, p.entry_price, p.entry_date, s.data->>'price' as current_price
                    FROM portfolio_items p
                    LEFT JOIN stock_cache s ON p.symbol = s.symbol
                    WHERE p.user_id = %s
                    ORDER BY p.entry_date DESC
                """, (user_id,))
                items = cur.fetchall()
                # Calculate return for each (using cached price if avail)
                # Note: This relies on cache being populated. If not, price might be null.
                self.wfile.write(json.dumps(items, default=str).encode('utf-8'))

            cur.close()
            return_db_connection(conn)

        except Exception as e:
            print(f"POST Error: {e}")
            # If headers not sent, send 500. But we sent 200 already.
            # So just return error JSON if possible
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))


    def _handle_leaderboard(self):
        self._set_headers()
        conn = get_db_connection()
        if not conn:
            self.wfile.write(json.dumps({"error": "Database unreachable"}).encode('utf-8'))
            return
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT u.nickname, p.symbol, p.entry_price, p.entry_date, s.data->>'price' as current_price
                FROM portfolio_items p
                JOIN users u ON p.user_id = u.id
                LEFT JOIN stock_cache s ON p.symbol = s.symbol
                ORDER BY p.entry_date DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            results = []
            for row in rows:
                curr = float(row['current_price']) if row['current_price'] else 0
                entry = float(row['entry_price'])
                ret = ((curr - entry) / entry) * 100 if curr > 0 else 0
                results.append({
                    "nickname": row['nickname'],
                    "symbol": row['symbol'],
                    "return": ret,
                    "date": row['entry_date']
                })
            self.wfile.write(json.dumps(results, default=str).encode('utf-8'))
            cur.close()
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            return_db_connection(conn)

    def _handle_stock_lookup(self, symbol):
        # Handle potential encoding issues from URL
        try:
            # If it's already a garbled string from incorrect decoding
            if 'Å' in symbol or 'ç' in symbol:
                symbol = symbol.encode('latin-1').decode('utf-8')
        except: pass

        symbol = symbol.strip()
        print(f"Stock Lookup: {symbol}")
        
        # 1. Reverse Lookup if Chinese name
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', symbol))
        if is_chinese:
            found = False
            # Exact match prioritization
            for ticker, name in TW_STOCK_NAMES.items():
                if symbol == name:
                    print(f"Found exact ticker {ticker} for {symbol}")
                    symbol = ticker
                    is_chinese = False 
                    found = True
                    break
            
            # Fuzzy match fallback
            if not found:
                for ticker, name in TW_STOCK_NAMES.items():
                    if symbol in name or name in symbol:
                        print(f"Found fuzzy ticker {ticker} for {symbol}")
                        symbol = ticker
                        is_chinese = False
                        found = True
                        break

        symbol = symbol.upper()

        # 2. Check Cache
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT data FROM stock_cache 
                    WHERE symbol = %s 
                    AND updated_at > NOW() - INTERVAL '5 minutes'
                """, (symbol,))
                cached_row = cur.fetchone()
                if cached_row:
                    response_data = cached_row['data']
                    response_data['source'] = 'cache'
                    self._set_headers()
                    self.wfile.write(json.dumps(response_data).encode('utf-8'))
                    cur.close()
                    return_db_connection(conn)
                    return
                cur.close()
            except Exception as e:
                print(f"Cache Read Error: {e}")
            finally:
                return_db_connection(conn)

        # 3. Fetch Fresh
        self._set_headers()
        try:
            is_us_stock = bool(re.search(r'[A-Za-z]', symbol)) and not is_chinese
            ss = StockScreener()
            if is_us_stock:
                ss.set_markets(tvs.Market.AMERICA)
            else:
                ss.set_markets(tvs.Market.TAIWAN)
            
            # Select necessary fields for SMC & Health
            ss.select(
                StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, 
                StockField.CHANGE, StockField.CHANGE_PERCENT, StockField.VOLUME,
                StockField.MARKET_CAPITALIZATION, StockField.SECTOR, StockField.INDUSTRY,
                StockField.RELATIVE_VOLUME, StockField.CHAIKIN_MONEY_FLOW_20,
                StockField.VOLUME_WEIGHTED_AVERAGE_PRICE, StockField.TECHNICAL_RATING,
                StockField.AVERAGE_TRUE_RANGE_14, StockField.RELATIVE_STRENGTH_INDEX_14,
                StockField.SIMPLE_MOVING_AVERAGE_20, StockField.SIMPLE_MOVING_AVERAGE_50, StockField.SIMPLE_MOVING_AVERAGE_200,
                StockField.WEEKLY_PERFORMANCE, StockField.MONTHLY_PERFORMANCE,
                StockField.YTD_PERFORMANCE, StockField.VOLATILITY,
                StockField.PIOTROSKI_F_SCORE_TTM, StockField.ALTMAN_Z_SCORE_TTM,
                StockField.GROSS_MARGIN_TTM, StockField.NET_MARGIN_TTM, StockField.OPERATING_MARGIN_TTM,
                StockField.EPS_DILUTED_TTM_YOY_GROWTH, StockField.REVENUE_TTM_YOY_GROWTH,
                StockField.PRICE_TO_EARNINGS_RATIO_TTM, StockField.PRICE_EARNINGS_GROWTH_TTM,
                StockField.GRAHAM_NUMBERS_TTM, StockField.RECOMMENDATION_MARK
            )

            if symbol.isdigit():
                 ss.add_filter(tvs.StockField.NAME, tvs.FilterOperator.EQUAL, symbol)
            elif not is_chinese:
                 ss.add_filter(tvs.StockField.NAME, tvs.FilterOperator.MATCH, symbol)
            
            df = ss.get()
            result = None
            if not df.empty:
                # tvscreener library often uses 'Symbol' for the ticker column
                symbol_col = 'Symbol' if 'Symbol' in df.columns else 'Name'
                
                # Local exact match filter
                mask = df[symbol_col] == symbol
                if mask.any():
                    result = df[mask]
                else:
                    # Fallback for Chinese names or other matches in Description
                    mask = df['Description'].str.contains(symbol, case=False, na=False)
                    if mask.any():
                        result = df[mask]

            # FALLBACK TO YFINANCE
            if result is None or result.empty:
                print(f"No match in tvscreener for {symbol}, trying yfinance...")
                yf_data = fetch_from_yfinance(symbol) # Helper below
                if yf_data:
                    self._save_to_cache(symbol, yf_data)
                    self.wfile.write(json.dumps(yf_data, default=str).encode('utf-8'))
                    return
                else:
                    self.wfile.write(json.dumps({"error": f"Symbol '{symbol}' not found"}).encode('utf-8'))
                    return
            
            # 4. Map & Analyze
            data = result.iloc[0].to_dict()
            symbol_col = 'Symbol' if 'Symbol' in data else 'Name'
            ticker = data.get(symbol_col, symbol)
            raw_name = data.get('Description', '')
            display_name = TW_STOCK_NAMES.get(ticker, raw_name) if not is_us_stock else raw_name
            
            price = data.get('Price', 0)
            target_price = data.get('Target Price (Average)', 0)
            if not is_us_stock and target_price > 0 and price > 0:
                if target_price < price * 0.1: # Proxy for currency mismatch
                    target_price *= 32.5

            # SMC & Radar Logic
            rvol = data.get('Relative Volume', 0)
            cmf = data.get('Chaikin Money Flow (20)', 0)
            vwap = data.get('Volume Weighted Average Price', 0)
            tech_rating = data.get('Technical Rating', 0)
            atr = data.get('Average True Range (14)', 2)
            
            smc_score = 0
            if rvol > 1.5: smc_score += 30
            if cmf > 0: smc_score += 30
            if price > vwap: smc_score += 20
            if tech_rating > 0: smc_score += 20

            response_data = {
                "symbol": ticker,
                "name": display_name,
                "price": price,
                "change": data.get('Change', 0),
                "changePercent": data.get('Change %', 0),
                "volume": data.get('Volume', 0),
                "marketCap": data.get('Market Capitalization', 0),
                "updatedAt": "Just now",
                "rvol": rvol, "cmf": cmf, "vwap": vwap,
                "technicalRating": tech_rating, 
                "analystRating": data.get('Analyst Rating', 3), 
                "targetPrice": target_price,
                "rsi": data.get('Relative Strength Index (14)', 50),
                "atr_p": atr,
                "sma20": data.get('Simple Moving Average (20)', 0),
                "sma50": data.get('Simple Moving Average (50)', 0),
                "sma200": data.get('Simple Moving Average (200)', 0),
                "perf_w": data.get('Weekly Performance', 0),
                "perf_m": data.get('Monthly Performance', 0),
                "perf_ytd": data.get('YTD Performance', 0),
                "volatility": data.get('Volatility', 0),
                "smcScore": smc_score,
                "prediction": {
                     "confidence": "高" if atr < 2 else "中",
                     "upper": price * (1 + (atr/100 * 3)),
                     "lower": price * (1 - (atr/100 * 3)),
                     "days": 3
                },
                "radarData": [
                    {"subject": "動能", "A": data.get('Relative Strength Index (14)', 50), "fullMark": 100},
                    {"subject": "趨勢", "A": (tech_rating + 1) * 50, "fullMark": 100},
                    {"subject": "關注", "A": min(100, rvol * 33), "fullMark": 100},
                    {"subject": "安全", "A": max(0, 100 - atr*10), "fullMark": 100},
                    {"subject": "價值", "A": (5 - data.get('Analyst Rating', 3)) * 25, "fullMark": 100}
                ],
                "sector": data.get('Sector', 'N/A'),
                "industry": data.get('Industry', 'N/A'),
                "fScore": data.get('Piotroski F-score', 0),
                "zScore": data.get('Altman Z-score', 0),
                "grossMargin": data.get('Gross Margin', 0),
                "netMargin": data.get('Net Margin', 0),
                "operatingMargin": data.get('Operating Margin', 0),
                "epsGrowth": data.get('EPS Diluted (TTM YoY Growth)', 0),
                "revGrowth": data.get('Revenue (TTM YoY Growth)', 0),
                "peRatio": data.get('Price to Earnings Ratio', 0),
                "pegRatio": data.get('PEG Ratio', 0),
                "grahamNumber": data.get("Graham's Number", 0)
            }
            
            # Sanitization
            for k, v in response_data.items():
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    response_data[k] = 0

            self._save_to_cache(symbol, response_data)
            self.wfile.write(json.dumps(response_data, default=str).encode('utf-8'))

        except Exception as e:
            print(f"Lookup Error: {e}")
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def _save_to_cache(self, symbol, response_data):
        conn = get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO stock_cache (symbol, data, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (symbol) 
                DO UPDATE SET data = EXCLUDED.data, updated_at = NOW();
            """, (symbol, json.dumps(response_data, default=str)))
            conn.commit()
            cur.close()
        except: pass
        finally: return_db_connection(conn)

    def do_GET(self):
        print(f"GET Request: {self.path}")
        try:
            query = parse_qs(urlparse(self.path).query)
            if 'leaderboard' in query:
                self._handle_leaderboard()
            elif 'symbol' in query:
                self._handle_stock_lookup(query['symbol'][0])
            else:
                self._set_headers()
                self.wfile.write(json.dumps({"error": "Invalid endpoint"}).encode('utf-8'))
        except Exception as e:
            print(f"Global GET Error: {e}")


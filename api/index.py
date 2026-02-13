from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
import re
import os
import time
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
}

# Database Utilities
try:
    from psycopg2 import pool
    # Initialize connection pool (minconn=1, maxconn=10)
    db_pool = pool.ThreadedConnectionPool(
        1, 10,
        os.environ['DATABASE_URL'],
        sslmode='require'
    )
    print("Database connection pool created.")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    db_pool = None

def get_db_connection():
    if db_pool:
        return db_pool.getconn()
    else:
        # Fallback if pool fails
        return psycopg2.connect(os.environ['DATABASE_URL'])

def return_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)
    elif conn:
        conn.close()

def init_db():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_cache (
                symbol TEXT PRIMARY KEY,
                data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
    finally:
        return_db_connection(conn)

# Initialize DB on start (Note: In pure serverless like Vercel, this might run on every cold start)
try:
    init_db()
except Exception as e:
    print(f"DB Init Error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        symbol = query_params.get('symbol', [None])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS
        self.end_headers()
        
        if not symbol:
            response = {"error": "Missing symbol parameters"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        symbol = symbol.strip().upper()

        # Check Cache
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if exists and is fresh (e.g., < 5 minutes old)
            cur.execute("""
                SELECT data FROM stock_cache 
                WHERE symbol = %s 
                AND updated_at > NOW() - INTERVAL '5 minutes'
            """, (symbol,))
            
            cached_row = cur.fetchone()
            
            if cached_row:
                # Cache Hit
                response_data = cached_row['data']
                response_data['source'] = 'cache'
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                cur.close()
                return_db_connection(conn)
                return
            
            # Cache Miss or Stale -> Fetch Fresh
            cur.close()
            # Don't return conn yet, we might reuse it or just get a new one later. 
            # Actually better to return it to pool and get it again to keep logic simple and safe 
            # or keep it open. Let's return it to be safe 
            return_db_connection(conn)
            conn = None

        except Exception as e:
            print(f"Cache Error: {e}")
            if conn: return_db_connection(conn)
            # Continue to fetch fresh if cache fails

        try:
            # Determine Market
            is_us_stock = bool(re.search(r'[A-Za-z]', symbol))
            
            ss = StockScreener()
            if is_us_stock:
                ss.set_markets(tvs.Market.AMERICA)
            else:
                ss.set_markets(tvs.Market.TAIWAN)
            
            df = ss.get()
            
            if df.empty:
                self.wfile.write(json.dumps({"error": "Stock not found"}).encode('utf-8'))
                return

            # Filter logic
            if 'Symbol' in df.columns:
                mask = df['Name'] == symbol
                if not mask.any() and 'Symbol' in df.columns:
                     mask = df['Symbol'].str.contains(symbol)
                result = df[mask]
            else:
                result = df
            
            if not result.empty:
                data = result.iloc[0].to_dict()
                
                # Name Logic
                raw_name = data.get('Description', '')
                ticker = data.get('Name', symbol)
                
                if not is_us_stock:
                    display_name = TW_STOCK_NAMES.get(ticker, raw_name)
                else:
                    display_name = raw_name

                # Target Price Logic
                target_price = data.get('Target Price (Average)', 0)
                price = data.get('Price', 0)
                
                if not is_us_stock and target_price > 0 and price > 0:
                    if target_price < price * 0.1:
                        potential_twd = target_price * 32.5
                        if 0.5 * price < potential_twd < 3.0 * price:
                             target_price = potential_twd
                        else:
                             target_price = 0
                
                # --- SMC Score Calculation ---
                smc_score = 0
                # 1. Volume Analysis (30pts)
                rvol = data.get('Relative Volume', 0)
                if rvol > 2.0: smc_score += 30
                elif rvol > 1.2: smc_score += 15
                
                # 2. Money Flow (30pts)
                cmf = data.get('Chaikin Money Flow (20)', 0)
                if cmf > 0.05: smc_score += 30
                elif cmf > 0: smc_score += 15
                
                # 3. Price vs VWAP (20pts)
                vwap = data.get('Volume Weighted Average Price', 0)
                if price > vwap: smc_score += 20
                
                # 4. Trend (20pts)
                if data.get('Technical Rating', 0) > 0.5: smc_score += 20
                elif data.get('Technical Rating', 0) > 0: smc_score += 10
                
                # --- Radar Data Calculation (Normalized 0-100) ---
                # Momentum: RSI (50 is neutral)
                rsi = data.get('Relative Strength Index (14)', 50)
                momentum_score = min(100, max(0, rsi)) # RSI itself is 0-100

                # Value: PE (Lower is better, typically) - Mock logic as PE might be missing
                # tvscreener doesn't always have PE. Use Perf as proxy for 'Growth/Value' mix if missing?
                # Let's use Analyst Rating as Value proxy (Strong Buy = good value?)
                # Analyst Rating: 1 (Strong Buy) to 5 (Sell). Inverse it.
                analyst_rating = data.get('Analyst Rating', 3)
                value_score = min(100, max(0, (5 - analyst_rating) * 25))
                
                # Safety: Inverse of Volatility/ATR
                # ATR %: 1% is safe, 5% is volatile. 
                atr = data.get('Average True Range % (14)', 2)
                safety_score = min(100, max(0, 100 - (atr * 10))) 
                
                # Trend: Technical Rating (-1 to 1) -> 0 to 100
                tech_rating = data.get('Technical Rating', 0)
                trend_score = min(100, max(0, (tech_rating + 1) * 50))
                
                # Attention: RVOL
                # RVOL 0.5 -> 0, RVOL 3.0 -> 100
                attention_score = min(100, max(0, (rvol * 33)))

                # --- Prediction Cone Calculation ---
                # Based on ATR, predict 3-5 days range
                # Daily ATR is atr_p (in %)
                # Confidence: Low if volatility is high, High if volatility is low?
                # Actually, in SMC, high vol at key level might be high confidence. 
                # Let's keep it simple: Squeeze (low vol) = High Confidence of breakout.
                
                prediction_confidence = "中"
                if atr < 1.5: prediction_confidence = "高 (波動收斂)"
                elif atr > 3.5: prediction_confidence = "低 (劇烈波動)"
                
                # 3-Day Range
                range_upper = price * (1 + (atr/100 * 3))
                range_lower = price * (1 - (atr/100 * 3))

                # Format for UI
                response_data = {
                    "symbol": ticker,
                    "name": display_name,
                    "price": price,
                    "change": data.get('Change', 0),
                    "changePercent": data.get('Change %', 0),
                    # ... existing fields ...
                    "volume": data.get('Volume', 0),
                    "marketCap": data.get('Market Capitalization', 0),
                    "updatedAt": "Just now",
                    "rvol": rvol,
                    "cmf": cmf,
                    "vwap": vwap,
                    "technicalRating": tech_rating, 
                    "analystRating": analyst_rating, 
                    "targetPrice": target_price,
                    "rsi": rsi,
                    "atr_p": atr,
                    "sma20": data.get('Simple Moving Average (20)', 0),
                    "sma50": data.get('Simple Moving Average (50)', 0),
                    "sma200": data.get('Simple Moving Average (200)', 0),
                    "perf_w": data.get('Weekly Performance', 0),
                    "perf_m": data.get('Monthly Performance', 0),
                    "perf_ytd": data.get('YTD Performance', 0),
                    "volatility": data.get('Volatility', 0),
                    "earningsDate": data.get('Upcoming Earnings Date', 0),
                    # New AI Data
                    "smcScore": smc_score,
                    "prediction": {
                         "confidence": prediction_confidence,
                         "upper": range_upper,
                         "lower": range_lower,
                         "days": 3
                    },
                    "radarData": [
                        {"subject": "動能 (Momentum)", "A": momentum_score, "fullMark": 100},
                        {"subject": "價值 (Value)", "A": value_score, "fullMark": 100},
                        {"subject": "安全性 (Safety)", "A": safety_score, "fullMark": 100},
                        {"subject": "趨勢 (Trend)", "A": trend_score, "fullMark": 100},
                        {"subject": "關注 (Attention)", "A": attention_score, "fullMark": 100},
                    ]
                }
                
                # Sanitization
                for k, v in response_data.items():
                    if v is None:
                        response_data[k] = 0
                    elif isinstance(v, float) and math.isnan(v):
                        response_data[k] = 0

                # Update Cache
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO stock_cache (symbol, data, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (symbol) 
                        DO UPDATE SET data = EXCLUDED.data, updated_at = NOW();
                    """, (symbol, json.dumps(response_data)))
                    conn.commit()
                    cur.close()
                    return_db_connection(conn)
                except Exception as e:
                    print(f"Cache Write Error: {e}")
                    if conn: return_db_connection(conn)

                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"error": f"Symbol '{symbol}' not found"}).encode('utf-8'))
                
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Internal Error: {str(e)}"}).encode('utf-8'))

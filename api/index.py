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
TW_STOCK_NAMES = {
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2303": "聯電",
    "2308": "台達電",
    "2412": "中華電",
    "2881": "富邦金",
    "2882": "國泰金",
    "2886": "兆豐金",
    "2891": "中信金",
    "1301": "台塑",
    "1303": "南亞",
    "1326": "台化",
    "6505": "台塑化",
    "2002": "中鋼",
    "2603": "長榮",
    "2609": "陽明",
    "2615": "萬海",
    "3008": "大立光",
    "3711": "日月光投控",
    "2884": "玉山金",
    "5880": "合庫金",
    "2892": "第一金",
    "2885": "元大金",
    "2880": "華南金",
    "2883": "開發金",
    "2887": "台新金",
    "2890": "永豐金",
    "3231": "緯創",
    "2382": "廣達",
    "2357": "華碩",
    "2356": "英業達",
    "2353": "宏碁",
    "2409": "友達",
    "3481": "群創",
}

# Database Utilities
def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    return conn

def init_db():
    conn = get_db_connection()
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
    conn.close()

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
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if exists and is fresh (e.g., < 5 minutes old)
            # Adjust interval as needed. '5 minutes' is a reasonable cache.
            cur.execute("""
                SELECT data FROM stock_cache 
                WHERE symbol = %s 
                AND updated_at > NOW() - INTERVAL '5 minutes'
            """, (symbol,))
            
            cached_row = cur.fetchone()
            
            if cached_row:
                # Cache Hit
                response_data = cached_row['data']
                response_data['source'] = 'cache' # Debug flag
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                cur.close()
                conn.close()
                return
            
            # Cache Miss or Stale -> Fetch Fresh
            cur.close()
            conn.close()

        except Exception as e:
            print(f"Cache Error: {e}")
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
                
                # Format for UI
                response_data = {
                    "symbol": ticker,
                    "name": display_name,
                    "price": price,
                    "change": data.get('Change', 0),
                    "changePercent": data.get('Change %', 0),
                    "volume": data.get('Volume', 0),
                    "marketCap": data.get('Market Capitalization', 0),
                    "updatedAt": "Just now",
                    "rvol": data.get('Relative Volume', 0),
                    "cmf": data.get('Chaikin Money Flow (20)', 0),
                    "vwap": data.get('Volume Weighted Average Price', 0),
                    "technicalRating": data.get('Technical Rating', 0), 
                    "analystRating": data.get('Analyst Rating', 3), 
                    "targetPrice": target_price,
                    "rsi": data.get('Relative Strength Index (14)', 50),
                    "atr_p": data.get('Average True Range % (14)', 0),
                    "sma20": data.get('Simple Moving Average (20)', 0),
                    "sma50": data.get('Simple Moving Average (50)', 0),
                    "sma200": data.get('Simple Moving Average (200)', 0),
                    "perf_w": data.get('Weekly Performance', 0),
                    "perf_m": data.get('Monthly Performance', 0),
                    "perf_ytd": data.get('YTD Performance', 0),
                    "volatility": data.get('Volatility', 0),
                    "earningsDate": data.get('Upcoming Earnings Date', 0)
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
                    conn.close()
                except Exception as e:
                    print(f"Cache Write Error: {e}")

                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"error": f"Symbol '{symbol}' not found"}).encode('utf-8'))
                
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Internal Error: {str(e)}"}).encode('utf-8'))

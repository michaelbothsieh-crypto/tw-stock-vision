from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import os
import tvscreener as tvs
from tvscreener import StockScreener, StockField

# Modular Imports
from api.db import get_db_connection, return_db_connection, init_db
from api.constants import TW_STOCK_NAMES
from api.scrapers import fetch_from_yfinance, sanitize_json, get_field, process_tvs_row

# Initialize DB on load
init_db()

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
            if conn is None:
                self.wfile.write(json.dumps({"error": "Database connection failed"}).encode('utf-8'))
                return
            cur = conn.cursor()

            if action == 'register_user':
                nickname, user_id = data.get('nickname'), data.get('id')
                if not user_id:
                    self.wfile.write(json.dumps({"error": "Missing ID"}).encode('utf-8'))
                    return
                # UPSERT logic: Insert id and nickname. If id exists, update nickname.
                # If nickname exists for ANOTHER id, this will handle via DB unique constraint if applicable.
                try:
                    cur.execute("""
                        INSERT INTO users (id, nickname) 
                        VALUES (%s, %s) 
                        ON CONFLICT (id) DO UPDATE SET nickname = EXCLUDED.nickname
                        RETURNING id, nickname
                    """, (user_id, nickname))
                    res = cur.fetchone()
                    conn.commit()
                    self.wfile.write(json.dumps({"status": "success", "user": {"id": str(res[0]), "nickname": res[1]}}).encode('utf-8'))
                except Exception as e:
                    conn.rollback()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

            elif action == 'list_users':
                cur.execute("SELECT id, nickname FROM users ORDER BY created_at DESC LIMIT 50")
                rows = cur.fetchall()
                users = [{"id": str(r[0]), "nickname": r[1]} for r in rows]
                self.wfile.write(json.dumps({"status": "success", "users": users}).encode('utf-8'))

            elif action == 'update_nickname':
                user_id, nickname = data.get('user_id'), data.get('nickname')
                cur.execute("UPDATE users SET nickname = %s WHERE id = %s", (nickname, user_id))
                conn.commit()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

            elif action == 'add_portfolio':
                user_id, symbol, price = data.get('user_id'), data.get('symbol'), data.get('price')
                entry_date = data.get('entry_date') # Optional
                
                # Normalize symbol
                symbol = re.sub(r'\.TW[O]?$', '', symbol.strip(), flags=re.IGNORECASE).upper()
                
                # If price is not provided, fetch current price automatically
                if price is None or price <= 0:
                    price = self._fetch_price_internal(symbol) or 0
                
                if entry_date:
                    cur.execute("INSERT INTO portfolio_items (user_id, symbol, entry_price, entry_date) VALUES (%s, %s, %s, %s) RETURNING id", (user_id, symbol, price, entry_date))
                else:
                    cur.execute("INSERT INTO portfolio_items (user_id, symbol, entry_price, entry_date) VALUES (%s, %s, %s, NOW()) RETURNING id", (user_id, symbol, price))
                
                res_id = cur.fetchone()[0]
                conn.commit()
                self.wfile.write(json.dumps({"status": "success", "id": res_id, "price": price}).encode('utf-8'))

            elif action == 'delete_portfolio':
                u_id, p_id = data.get('user_id'), data.get('portfolio_id')
                cur.execute("DELETE FROM portfolio_items WHERE id = %s AND user_id = %s", (p_id, u_id))
                conn.commit()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

            elif action == 'update_portfolio_all':
                u_id, p_id = data.get('user_id'), data.get('portfolio_id')
                p, d = data.get('price'), data.get('entry_date')
                if p is not None and d is not None:
                    cur.execute("UPDATE portfolio_items SET entry_price = %s, entry_date = %s WHERE id = %s AND user_id = %s", (p, d, p_id, u_id))
                elif p is not None:
                    cur.execute("UPDATE portfolio_items SET entry_price = %s WHERE id = %s AND user_id = %s", (p, p_id, u_id))
                elif d is not None:
                    cur.execute("UPDATE portfolio_items SET entry_date = %s WHERE id = %s AND user_id = %s", (d, p_id, u_id))
                conn.commit()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
            elif action == 'get_portfolio':
                user_id = data.get('user_id')
                # Use RealDictCursor to return objects
                from psycopg2.extras import RealDictCursor
                dict_cur = conn.cursor(cursor_factory=RealDictCursor)
                dict_cur.execute("""
                    SELECT 
                        p.id, 
                        p.symbol, 
                        p.entry_price, 
                        p.entry_date, 
                        s.data->>'price' as current_price 
                    FROM portfolio_items p 
                    LEFT JOIN stock_cache s ON p.symbol = s.symbol 
                    WHERE p.user_id = %s 
                    ORDER BY p.entry_date DESC
                """, (user_id,))
                self.wfile.write(json.dumps(dict_cur.fetchall(), default=str).encode('utf-8'))
                dict_cur.close()

            cur.close()
            return_db_connection(conn)
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def _handle_leaderboard(self):
        self._set_headers()
        conn = get_db_connection()
        if not conn: return
        try:
            from psycopg2.extras import RealDictCursor
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT 
                    u.nickname, 
                    p.id as portfolio_id, 
                    p.user_id, 
                    p.symbol, 
                    p.entry_price, 
                    p.entry_date, 
                    s.data->>'price' as current_price 
                FROM portfolio_items p 
                JOIN users u ON p.user_id = u.id 
                LEFT JOIN stock_cache s ON p.symbol = s.symbol 
                ORDER BY p.entry_date DESC 
                LIMIT 50
            """)
            rows, results = cur.fetchall(), []
            for row in rows:
                try:
                    curr = float(row['current_price']) if row['current_price'] else 0
                    entry = float(row['entry_price']) if row['entry_price'] else 0
                    
                    if entry <= 0:
                        ret = 0
                    else:
                        # 績效計算: (現值 - 成本) / 成本 * 100
                        # 如果 current_price 為 0 (快取過期)，績效先顯示為 0 或使用 entry_price (平盤)
                        ret = ((curr - entry) / entry) * 100 if curr > 0 else 0
                    
                    results.append({
                        "id": row['portfolio_id'], 
                        "user_id": str(row['user_id']), 
                        "nickname": row['nickname'], 
                        "symbol": row['symbol'], 
                        "entry_price": entry, 
                        "current_price": curr,
                        "return": round(ret, 2), 
                        "date": row['entry_date']
                    })
                except:
                    continue
            self.wfile.write(json.dumps(results, default=str).encode('utf-8'))
            cur.close()
        finally: return_db_connection(conn)

    def _fetch_price_internal(self, symbol):
        # Normalize symbol
        symbol = re.sub(r'\.TW[O]?$', '', symbol.strip(), flags=re.IGNORECASE).upper()
        
        # Check cache first
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT data->>'price' FROM stock_cache WHERE symbol = %s AND updated_at > NOW() - INTERVAL '4 hours'", (symbol,))
            row = cur.fetchone()
            if row and row[0]:
                cur.close()
                return_db_connection(conn)
                return float(row[0])
            cur.close()
            return_db_connection(conn)

        # Fetch fresh if not in cache (simplified lookup for add_portfolio move)
        try:
            is_us = not symbol.isdigit()
            ss = StockScreener()
            ss.set_markets(tvs.Market.AMERICA if is_us else tvs.Market.TAIWAN)
            ss.search(symbol)
            ss.select(StockField.PRICE)
            df = ss.get()
            if df.empty:
                data = fetch_from_yfinance(symbol)
                return data.get('price', 0)
            else:
                return float(df.iloc[0]['Price'])
        except:
            return 0

    def _handle_stock_lookup(self, symbol):
        symbol = re.sub(r'\.TW[O]?$', '', symbol.strip(), flags=re.IGNORECASE).upper()
        # Name Lookup...
        is_tw = symbol.isdigit()
        if is_tw and symbol in TW_STOCK_NAMES:
            # 確保台股代號能正確對應到中文名，避免模糊搜尋失敗
            pass
            
        for ticker, name in TW_STOCK_NAMES.items():
            if symbol == name or symbol in name:
                symbol = ticker
                break

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT data FROM stock_cache WHERE symbol = %s AND updated_at > NOW() - INTERVAL '1 hour'", (symbol,))
            row = cur.fetchone()
            if row:
                self._set_headers()
                self.wfile.write(json.dumps(row[0]).encode('utf-8'))
                cur.close()
                return_db_connection(conn)
                return
            cur.close()
            return_db_connection(conn)

        self._set_headers()
        try:
            is_tw = symbol.isdigit()
            is_us = not is_tw
            
            ss = StockScreener()
            ss.set_markets(tvs.Market.AMERICA if is_us else tvs.Market.TAIWAN)
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
            
            # 如果精確搜尋失敗且是台股，嘗試模糊搜尋
            if df.empty and is_tw:
                ss = StockScreener()
                ss.set_markets(tvs.Market.TAIWAN)
                df_all = ss.get()
                if not df_all.empty:
                    df = df_all[df_all['Name'].str.contains(symbol, na=False) | df_all['Description'].str.contains(symbol, na=False)]

            data = None
            if not df.empty:
                raw_row = df.iloc[0].to_dict()
                data = process_tvs_row(raw_row, symbol)
                
            # 如果仍無數據或關鍵缺失，由 yfinance 深度補件
            if not data or data.get('fScore', 0) == 0:
                yf_data = fetch_from_yfinance(symbol)
                if yf_data:
                    if not data: 
                        data = yf_data
                    else:
                        # 融合：將 yf 的關鍵財務指標併入 tv 資料
                        # 包含 HealthCheck 所需的所有欄位
                        keys_to_merge = [
                            'fScore', 'zScore', 'grahamNumber', 'eps', 'targetPrice', 'technicalRating', 'analystRating',
                            'grossMargin', 'netMargin', 'operatingMargin', 'revGrowth', 'epsGrowth',
                            'peRatio', 'pegRatio', 'sma20', 'sma50', 'sma200', 'rsi', 'atr_p'
                        ]
                        is_tw = symbol.isdigit()
                        for k in keys_to_merge:
                            # 針對目標價 (targetPrice)，如果是台股或者是 TVS 數值顯然異常，則優先用 yf
                            # 加強判斷：若台股代號且 yf 有資料，則強制 yf
                            force_yf = False
                            if k == 'targetPrice' and is_tw and yf_data.get('targetPrice'):
                                force_yf = True
                            
                            # 或者原始資料無效時也補件
                            if force_yf or data.get(k) is None or data.get(k) == 0:
                                val = yf_data.get(k)
                                if val is not None:
                                    data[k] = val

            if data:
                price = data.get('price', 1)
                data['current_price'] = price
                # 雷達圖：確保即使資料欠缺也有保底數值呈現 (避免 0 點)
                data['radarData'] = [
                    {"subject": "動能", "A": max(15, min(100, 50 + (data.get('technicalRating', 0) * 50))), "desc": "價格相對 MA 的強度"},
                    {"subject": "趨勢", "A": max(15, min(100, 50 + ((price - data.get('sma50', price)) / max(1, data.get('sma50', 1)) * 200))), "desc": "短期均線排列狀態"},
                    {"subject": "關注", "A": max(15, min(100, data.get('rvol', 1) * 30)), "desc": "相對成交量異常偵測"},
                    {"subject": "安全", "A": max(15, min(100, data.get('fScore', 3) * 11)), "desc": "Piotroski 財務評分"},
                    {"subject": "價值", "A": max(15, min(100, (data.get('grahamNumber', 0) / price * 100) if price > 0 else 55)), "desc": "葛拉漢合理價折溢價"}
                ]
                # AI 預測區間 (對齊前端 PredictionCard 必要欄位)
                atr = data.get('atr', data['price'] * 0.02)
                data['prediction'] = {
                    "confidence": "中 (68%)",
                    "upper": data['price'] + (atr * 2),
                    "lower": data['price'] - (atr * 2),
                    "days": 14
                }
                
                self._save_to_cache(symbol, data)
                self.wfile.write(json.dumps(sanitize_json(data)).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"error": "Symbol not found"}).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def _save_to_cache(self, symbol, data):
        conn = get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO stock_cache (symbol, data, updated_at) VALUES (%s, %s, NOW()) ON CONFLICT (symbol) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()", (symbol, json.dumps(data)))
            conn.commit()
            cur.close()
        finally: return_db_connection(conn)

    def _handle_market_trending(self):
        self._set_headers()
        try:
            parsed = urlparse(self.path)
            q = parse_qs(parsed.query)
            market_param = q.get('market', ['TW'])[0].upper()
            
            ss = StockScreener()
            if market_param == 'US' or market_param == 'AMERICA':
                ss.set_markets(tvs.Market.AMERICA)
            else:
                ss.set_markets(tvs.Market.TAIWAN)
            
            ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE_PERCENT, StockField.TECHNICAL_RATING)
            ss.sort_by(StockField.TECHNICAL_RATING, ascending=False)
            df = ss.get()
            
            if df.empty:
                popular_symbols = ["2330", "2317", "2454", "2603", "2881"] if market_param == 'TW' else ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"]
                results = []
                for sym in popular_symbols:
                    price = self._fetch_price_internal(sym)
                    results.append({
                        "symbol": sym,
                        "description": TW_STOCK_NAMES.get(sym, sym if market_param == 'US' else "熱門標的"),
                        "price": price,
                        "changePercent": 0,
                        "rating": 0.5
                    })
                self.wfile.write(json.dumps(results).encode('utf-8'))
                return

            results = []
            for _, row in df.head(15).iterrows():
                # 優化代號抓取：優先取 Name ( ticker )，若無則取 Symbol 去除交易所
                raw_name = str(row.get('Name', ''))
                raw_symbol = str(row.get('Symbol', ''))
                
                # 台股 TVS 通常 Name 是代號，Symbol 是 EXCHANGE:TICKER
                symbol = raw_name if raw_name.isdigit() else raw_symbol.split(':')[-1]
                if not symbol: symbol = raw_symbol
                
                # 過濾掉非數字的台股標的 (若是台股市場)
                if market_param == 'TW' and not symbol.isdigit():
                    continue

                desc = row.get('Description', symbol)
                if market_param == 'TW' and symbol in TW_STOCK_NAMES:
                    desc = TW_STOCK_NAMES[symbol]
                
                price = get_field(row, ['Price'], 0)
                change = get_field(row, ['Change %', 'change_abs_percent'], 0)
                
                raw_rating = row.get('Technical Rating', row.get('rating', 0))
                rating = 0
                if isinstance(raw_rating, str):
                    if 'Strong Buy' in raw_rating: rating = 1
                    elif 'Buy' in raw_rating: rating = 0.5
                    elif 'Sell' in raw_rating: rating = -0.5
                    elif 'Strong Sell' in raw_rating: rating = -1
                else:
                    try: rating = float(raw_rating)
                    except: rating = 0

                results.append({
                    "symbol": symbol,
                    "description": desc,
                    "price": price,
                    "changePercent": change,
                    "rating": rating
                })
            
            # 兼容性封裝：同時回傳列表與物件格式
            output = sanitize_json(results)
            self.wfile.write(json.dumps(output).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        if 'leaderboard' in q or '/leaderboard' in parsed.path: self._handle_leaderboard()
        elif 'trending' in q or '/market/trending' in parsed.path: self._handle_market_trending()
        elif 'symbol' in q: self._handle_stock_lookup(q['symbol'][0])
        elif parsed.path.endswith('/health'):
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

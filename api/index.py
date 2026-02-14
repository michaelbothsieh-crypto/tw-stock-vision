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
                if not nickname or not user_id:
                    self.wfile.write(json.dumps({"error": "Missing params"}).encode('utf-8'))
                    return
                cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if cur.fetchone():
                    cur.execute("UPDATE users SET nickname = %s WHERE id = %s", (nickname, user_id))
                else:
                    cur.execute("INSERT INTO users (id, nickname) VALUES (%s, %s)", (user_id, nickname))
                conn.commit()
                self.wfile.write(json.dumps({"status": "success", "user": {"id": user_id, "nickname": nickname}}).encode('utf-8'))

            elif action == 'update_nickname':
                user_id, nickname = data.get('user_id'), data.get('nickname')
                cur.execute("UPDATE users SET nickname = %s WHERE id = %s", (nickname, user_id))
                conn.commit()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))

            elif action == 'add_portfolio':
                user_id, symbol, price = data.get('user_id'), data.get('symbol'), data.get('price')
                entry_date = data.get('entry_date') # Optional
                
                # If price is not provided, fetch current price automatically
                if price is None or price <= 0:
                    price = self._fetch_price_internal(symbol) or 0
                
                if entry_date:
                    cur.execute("INSERT INTO portfolio_items (user_id, symbol, entry_price, entry_date) VALUES (%s, %s, %s, %s)", (user_id, symbol, price, entry_date))
                else:
                    cur.execute("INSERT INTO portfolio_items (user_id, symbol, entry_price, entry_date) VALUES (%s, %s, %s, NOW())", (user_id, symbol, price))
                conn.commit()
                self.wfile.write(json.dumps({"status": "success", "price": price}).encode('utf-8'))

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
                cur.execute("SELECT p.id, p.symbol, p.entry_price, p.entry_date, s.data->>'price' as current_price FROM portfolio_items p LEFT JOIN stock_cache s ON p.symbol = s.symbol WHERE p.user_id = %s ORDER BY p.entry_date DESC", (user_id,))
                self.wfile.write(json.dumps(cur.fetchall(), default=str).encode('utf-8'))

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
            cur.execute("SELECT u.nickname, p.id as portfolio_id, p.user_id, p.symbol, p.entry_price, p.entry_date, s.data->>'price' as current_price FROM portfolio_items p JOIN users u ON p.user_id = u.id LEFT JOIN stock_cache s ON p.symbol = s.symbol ORDER BY p.entry_date DESC LIMIT 20")
            rows, results = cur.fetchall(), []
            for row in rows:
                curr = float(row['current_price']) if row['current_price'] else 0
                entry = float(row['entry_price'])
                ret = ((curr - entry) / entry) * 100 if curr > 0 else 0
                results.append({"id": row['portfolio_id'], "user_id": str(row['user_id']), "nickname": row['nickname'], "symbol": row['symbol'], "entry_price": row['entry_price'], "return": ret, "date": row['entry_date']})
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
            is_us = not symbol.isdigit()
            ss = StockScreener()
            ss.set_markets(tvs.Market.AMERICA if is_us else tvs.Market.TAIWAN)
            ss.search(symbol)
            ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, StockField.CHANGE, StockField.CHANGE_PERCENT, 
                      StockField.VOLUME, StockField.MARKET_CAPITALIZATION, StockField.SECTOR, StockField.INDUSTRY, StockField.EXCHANGE,
                      StockField.RELATIVE_VOLUME, StockField.CHAIKIN_MONEY_FLOW_20, StockField.VOLUME_WEIGHTED_AVERAGE_PRICE, 
                      StockField.TECHNICAL_RATING, StockField.AVERAGE_TRUE_RANGE_14, StockField.RELATIVE_STRENGTH_INDEX_14,
                      StockField.SIMPLE_MOVING_AVERAGE_50, StockField.SIMPLE_MOVING_AVERAGE_200, 
                      StockField.PIOTROSKI_F_SCORE_TTM, StockField.BASIC_EPS_TTM, StockField.RECOMMENDATION_MARK,
                      StockField.PRICE_TARGET_MEAN)
            df = ss.get()
            
            if df.empty:
                data = fetch_from_yfinance(symbol)
            else:
                raw_row = df.iloc[0].to_dict()
                data = process_tvs_row(raw_row, symbol)
                
                # 回填: 若目標價或評級仍為 0, 使用 yfinance 補齊
                if not data.get('targetPrice') or data.get('technicalRating') == 0:
                    yf_f = fetch_from_yfinance(symbol)
                    if yf_f:
                        if not data.get('targetPrice'): data['targetPrice'] = yf_f.get('targetPrice', 0)
                        if data.get('technicalRating') == 0: data['technicalRating'] = yf_f.get('technicalRating', 0)
                        # 補齊財務三率
                        data.update({
                            "grossMargin": yf_f.get('grossMargin', 0),
                            "netMargin": yf_f.get('netMargin', 0),
                            "operatingMargin": yf_f.get('operatingMargin', 0)
                        })

            if data:
                # 生成雷達圖數據 (Scoring)
                data['radarData'] = [
                    {"subject": "動能", "A": min(100, max(0, 50 + (data.get('technicalRating', 0) * 50)))},
                    {"subject": "趨勢", "A": min(100, max(0, 50 + ((data.get('price', 1) - data.get('sma50', 1)) / data.get('sma50', 1) * 200)))},
                    {"subject": "關注", "A": min(100, data.get('rvol', 1) * 30)},
                    {"subject": "安全", "A": min(100, data.get('fScore', 5) * 11)},
                    {"subject": "價值", "A": min(100, (data.get('grahamNumber', 0) / data.get('price', 1) * 100) if data.get('price', 0) > 0 else 50)}
                ]
                # AI 預測區間
                data['prediction'] = {
                    "high": data['price'] + (data.get('atr', data['price']*0.02) * 2),
                    "low": data['price'] - (data.get('atr', data['price']*0.02) * 2)
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

    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        if 'leaderboard' in q or '/leaderboard' in parsed.path: self._handle_leaderboard()
        elif 'symbol' in q: self._handle_stock_lookup(q['symbol'][0])
        elif parsed.path.endswith('/health'):
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

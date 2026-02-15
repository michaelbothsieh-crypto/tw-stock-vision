from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import os
import math
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

    def _handle_stock_lookup(self, symbol, q):
        symbol = re.sub(r'\.TW[O]?$', '', symbol.strip(), flags=re.IGNORECASE).upper()
        # Name Lookup...
        
        for ticker, name in TW_STOCK_NAMES.items():
            if symbol == name or symbol in name:
                symbol = ticker
                break

        conn = get_db_connection()
        if conn:
            # 加入 flush 支援：若 query 中有 flush=true 則跳過緩存讀取
            do_flush = q.get('flush', ['false'])[0].lower() == 'true'
            if not do_flush:
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
            # 改良市場偵測邏輯：包含中文或純數字 -> 台股；其餘 -> 美股
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', symbol))
            is_digit = symbol.isdigit()
            
            is_tw = has_chinese or is_digit
            is_us = not is_tw
            
            # 如果是台股且為數字，確保為 4-6 位數，否則可能是美股純數字代號（較少見但防呆）
            if is_digit and len(symbol) > 6:
                is_tw = False
                is_us = True

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
                       StockField.ALTMAN_Z_SCORE_TTM, StockField.GRAHAM_NUMBERS_TTM, StockField.PRICE_TARGET_AVERAGE,
                       StockField.RETURN_ON_EQUITY_TTM, StockField.RETURN_ON_ASSETS_TTM, StockField.DEBT_TO_EQUITY_RATIO_MRQ,
                       StockField.REVENUE_TTM_YOY_GROWTH, StockField.NET_INCOME_TTM_YOY_GROWTH, StockField.YIELD_RECENT)
            df = ss.get()
            
            # 如果精確搜尋失敗且是台股，嘗試模糊搜尋
            if df.empty and is_tw:
                print(f"[Search Fallback] Precise search failed for {symbol}, trying fuzzy match...")
                ss_fuzzy = StockScreener()
                ss_fuzzy.set_markets(tvs.Market.TAIWAN)
                df_all = ss_fuzzy.get()
                if not df_all.empty:
                    mask = (df_all['Description'].str.contains(symbol, na=False, case=False)) | \
                           (df_all['Name'].str.contains(symbol, na=False, case=False))
                    df = df_all[mask]

            data = None
            if not df.empty:
                raw_row = df.iloc[0].to_dict()
                # 重要：獲取正確的代號，否則 yfinance 會抓不到
                actual_symbol = raw_row.get('Name', symbol)
                data = process_tvs_row(raw_row, actual_symbol)
                symbol = actual_symbol # 更新為代號
                
            # 如果仍無數據、關鍵缺失、或 F-Score 為 0 (台股 TVS 常缺失)，由 yfinance 補件
            if not data or data.get('fScore', 0) == 0 or data.get('eps') is None or data.get('roe') == 0:
                yf_data = fetch_from_yfinance(symbol)
                if yf_data:
                    if not data: 
                        data = yf_data
                    else:
                        yf_price = yf_data.get('price', 0)
                        tvs_price = data.get('price', 0)
                        
                        if yf_price > 0 and tvs_price > 0 and abs(yf_price - tvs_price) / tvs_price > 0.5:
                            print(f"[Data Leak Prevention] Dropping yf data for {symbol}")
                        else:
                            keys_to_merge = [
                                'fScore', 'zScore', 'grahamNumber', 'eps', 'targetPrice', 'technicalRating', 'analystRating',
                                'grossMargin', 'netMargin', 'operatingMargin', 'revGrowth', 'epsGrowth',
                                'peRatio', 'pegRatio', 'sma20', 'sma50', 'sma200', 'rsi', 'atr_p', 'marketCap',
                                'roe', 'roa', 'debtToEquity', 'revGrowth', 'netGrowth', 'yield'
                            ]
                            for k in keys_to_merge:
                                yf_val = yf_data.get(k)
                                if yf_val is None:
                                    continue

                                # 針對目標價 (targetPrice) 實施嚴格異常攔截
                                if k == 'targetPrice':
                                    curr_p = data.get('price', 1)
                                    tvs_val = data.get(k, 0)
                                    
                                    # 異常識別：若 yf 數值與現價偏離超過 50%
                                    is_yf_extreme = (yf_val > 0 and curr_p > 0 and abs(yf_val - curr_p) / curr_p > 0.5)
                                    # 若 TVS 數值與現價偏離超過 50% (通常是單位錯誤，如美金 vs 台幣)
                                    is_tvs_extreme = (tvs_val > 0 and curr_p > 0 and abs(tvs_val - curr_p) / curr_p > 0.5)

                                    # 邏輯 A：如果 yf 數值極度異常，且 TVS 已經有一個更合理的目標價或是 yf 跟現價比太扯，則攔截
                                    if is_yf_extreme:
                                        if not is_tvs_extreme and tvs_val > 0:
                                            continue # 保留 TVS，捨棄異常 yf
                                        # 如果兩邊都極端或 TVS 沒資料，且與現價偏離超過 80% (通常是匯率/單位錯誤)，則攔截
                                        if abs(yf_val - curr_p) / curr_p > 0.8: 
                                            continue
                                    
                                    # 邏輯 B：決定是否覆蓋
                                    if is_tvs_extreme or tvs_val == 0 or is_tw:
                                        if not is_yf_extreme:
                                            data[k] = yf_val
                                
                                # 其他一般欄位補件 (ROE, ROA, Debt, etc.)
                                elif data.get(k) is None or data.get(k) == 0:
                                    data[k] = yf_val

            if data:
                # --- 核心強化：財經體質標籤 (Health Label) ---
                roe = data.get('roe', 0)
                z_score = data.get('zScore', 0)
                debt = data.get('debtToEquity', 100)
                
                health_label = "普"
                if roe > 15 and z_score > 2.5: health_label = "優"
                elif roe > 8 and z_score > 1.2: health_label = "良"
                elif roe < 0 or z_score < 0.5 or debt > 150: health_label = "差"
                data['healthLabel'] = health_label

                # --- 核心強化：成長預測 (Growth Projection) ---
                rev_g = data.get('revGrowth', 0)
                f_score = data.get('fScore', 0)
                projection = "持平"
                if rev_g > 20 and f_score >= 6: projection = "高速成長"
                elif rev_g > 5: projection = "溫和成長"
                elif rev_g < -10: projection = "衰退警戒"
                data['growthProjection'] = projection

                price = data.get('price', 1)
                # 雷達圖算法優化
                safe_val = (data.get('fScore', 3) * 10) + max(0, 30 - data.get('debtToEquity', 100) / 4)
                momentum_val = 50 + (data.get('technicalRating', 0) * 30) + (data.get('revGrowth', 0) * 0.5)
                value_val = (data.get('grahamNumber', 0) / price * 60) + (data.get('grossMargin', 0) * 0.4) if price > 0 else 50
                trend_val = 50 + ((price - data.get('sma50', price)) / max(1, data.get('sma50', 1)) * 150)
                mcap_score = 40 + (math.log10(max(1e9, data.get('marketCap', 1e9))) / 12 * 40) if isinstance(data.get('marketCap'), (int, float)) else 60

                data['radarData'] = [
                    {"subject": "動能", "A": max(15, min(100, momentum_val)), "desc": "結合技術強弱與營收成長"},
                    {"subject": "趨勢", "A": max(15, min(100, trend_val)), "desc": "中短期均線排列狀態"},
                    {"subject": "規模", "A": max(15, min(100, mcap_score)), "desc": "市場規模與資本厚度"},
                    {"subject": "安全", "A": max(15, min(100, safe_val)), "desc": "財務結構與債信評估"},
                    {"subject": "價值", "A": max(15, min(100, value_val)), "desc": "合理價折價與利潤空間"}
                ]
                
                t_price = data.get('targetPrice', 0)
                if t_price > 0:
                    upside = ((t_price - price) / price) * 100
                    data['upside'] = round(upside, 2)

                # AI 預測區間
                atr = data.get('atr', price * 0.02)
                data['prediction'] = {
                    "confidence": "中 (68%)" if data.get('fScore', 0) > 4 else "低 (45%)",
                    "upper": price + (atr * 2),
                    "lower": price - (atr * 2),
                    "days": 14
                }
                
                self._save_to_cache(symbol, data)
                self.wfile.write(json.dumps(sanitize_json(data)).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"error": "Unable to fetch data", "symbol": symbol}).encode('utf-8'))
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
                # 若 TVS 失效，回退到預定義的熱門標的
                if market_param == 'TW':
                    popular = [
                        ("2330", "台積電"), ("2317", "鴻海"), ("2454", "聯發科"), 
                        ("2603", "長榮"), ("2881", "富邦金"), ("2308", "台達電"),
                        ("2382", "廣達"), ("2882", "國泰金"), ("3711", "日月光投控")
                    ]
                else:
                    popular = [
                        ("NVDA", "NVIDIA"), ("AAPL", "Apple"), ("TSLA", "Tesla"),
                        ("MSFT", "Microsoft"), ("GOOGL", "Google"), ("AMZN", "Amazon"),
                        ("META", "Meta"), ("AVGO", "Broadcom"), ("LLY", "Eli Lilly")
                    ]
                
                results = []
                for sym, name in popular:
                    price = self._fetch_price_internal(sym)
                    results.append({
                        "symbol": sym,
                        "description": name,
                        "price": price,
                        "changePercent": 0,
                        "rating": 0.5
                    })
                self.wfile.write(json.dumps(sanitize_json(results)).encode('utf-8'))
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
        elif 'symbol' in q: self._handle_stock_lookup(q['symbol'][0], q)
        elif parsed.path.endswith('/health'):
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

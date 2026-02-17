import re
import json
import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField
from api.db import get_db_connection, return_db_connection
from api.constants import TW_STOCK_NAMES
from api.scrapers import fetch_from_yfinance, fetch_history_from_yfinance, sanitize_json, get_field, process_tvs_row, trunc2, calculate_rsi

class StockService:
    @staticmethod
    def get_current_price(symbol):
        # Normalize symbol
        symbol = re.sub(r'\.TW[O]?$', '', symbol.strip(), flags=re.IGNORECASE).upper()
        
        # Check cache only
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT data->>'price' FROM stock_cache WHERE symbol = %s", (symbol,))
                row = cur.fetchone()
                if row and row[0]:
                    return float(row[0])
            except:
                pass
            finally:
                return_db_connection(conn)
        return 0

    @staticmethod
    def get_leaderboard():
        conn = get_db_connection()
        if not conn: return []
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
            return results
        finally: return_db_connection(conn)

    @staticmethod
    def get_market_trending(market_param):
        market_param = market_param.upper()
        
        # READ-ONLY from DB
        # Query stock_cache for cached records
        # Filter by simple heuristics (e.g., volume > 0, updated recently)
        # Ideally, we should have a 'trending' flag or table, but for now, 
        # let's return the most recently updated stocks in cache.
        
        conn = get_db_connection()
        if not conn: return []
        
        results = []
        try:
            cur = conn.cursor()
            # Fetch top 20 recently updated stocks
            # data is JSONB, we can extract fields
            cur.execute("""
                SELECT symbol, data 
                FROM stock_cache 
                WHERE updated_at > NOW() - INTERVAL '24 hours' 
                ORDER BY updated_at DESC, (data->>'volume')::numeric DESC NULLS LAST
                LIMIT 20
            """)
            rows = cur.fetchall()
            
            for r in rows:
                symbol, data_json = r
                if isinstance(data_json, str):
                    data = json.loads(data_json)
                else:
                    data = data_json

                results.append(data)
                
            cur.close()
        except Exception as e:
            print(f"Error fetching trending from DB: {e}")
            return []
        finally:
            return_db_connection(conn)
            
        return sanitize_json(results)

    @staticmethod
    def get_stock_details(symbol, period='1y', interval='1d', flush=False):
        symbol = re.sub(r'\.TW[O]?$', '', symbol.strip(), flags=re.IGNORECASE).upper()
        
        # Try to resolve name from DB
        conn = get_db_connection()
        if not conn: return None
        
        try:
            # Name Lookup via DB
            cur = conn.cursor()
            # Check if symbol exists in stock_names (could use like search for name?)
            # For now, precise match on symbol or name
            # Optimization: Just use memory TW_STOCK_NAMES if available, but we want DB source of truth
            cur.execute("SELECT symbol, name FROM stock_names WHERE symbol = %s OR name = %s LIMIT 1", (symbol, symbol))
            name_row = cur.fetchone()
            if name_row:
                symbol = name_row[0] # Canonical symbol
            cur.close()

            # Flush -> Force update (Called by Updater Service usually)
            if flush:
                return StockService._fetch_and_cache(symbol, period, interval)

            # Normal Read -> DB Cache Only
            cur = conn.cursor()
            cur.execute("SELECT data FROM stock_cache WHERE symbol = %s", (symbol,))
            row = cur.fetchone()
            cur.close()
            
            if row:
                cached_data = dict(row[0]) if isinstance(row[0], dict) else {}
                
                # OPTIONAL: Fetch History on demand?
                # For strict "no external" policy, history should be in DB or Client-side.
                # However, history is large. 
                # Decision: Keep history fetch for now as it doesn't block STARTUP, 
                # but it does block request.
                # To be truly non-blocking, history should be removed or cached.
                # Let's try fetching history if missing from cache (it's not in cache usually)
                # ERROR: logic in original code was: fetch history and add to cached_data
                # If we want speed, we should skip history or fetch it async.
                # But frontend needs it for sparks?
                # Let's keep history fetch but with timeout?
                # Accessing yfinance here violates "Read Only".
                # But without history, charts break.
                # Compromise: Try to fetch history, but if it fails/slows, return without it.
                # Better: Allow history fetch for now, but optimize `sync_names.py` to NOT do it.
                
                history = fetch_history_from_yfinance(symbol, period=period, interval=interval)
                if history:
                    cached_data["history"] = history
                
                return sanitize_json(cached_data)
            
            return None # 404 if not in cache

        finally:
            return_db_connection(conn)

    @staticmethod
    def _fetch_and_cache(symbol, period, interval):
        """
        Internal method to fetch from external sources (Yahoo/TVS).
        Used by Updater Service via flush=True.
        """
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', symbol))
        is_digit = symbol.isdigit()
        is_tw = has_chinese or is_digit
        is_us = not is_tw
        
        if is_digit and len(symbol) > 6:
            is_tw = False
            is_us = True

        try:
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
                       StockField.REVENUE_TTM_YOY_GROWTH, StockField.NET_INCOME_TTM_YOY_GROWTH, StockField.YIELD_RECENT,
                       StockField.PRICE_TO_EARNINGS_RATIO_TTM, StockField.PRICE_TO_BOOK_MRQ, StockField.DIVIDEND_YIELD_FORWARD,
                       StockField.EPS_DILUTED_TTM_YOY_GROWTH, StockField.CURRENT_RATIO_MRQ, StockField.QUICK_RATIO_MRQ,
                       StockField.FREE_CASH_FLOW_TTM)
            df = ss.get()
        except:
            df = None

        if (df is None or df.empty) and is_tw:
            ss_fuzzy = StockScreener()
            ss_fuzzy.set_markets(tvs.Market.TAIWAN)
            try:
                df_all = ss_fuzzy.get()
                if not df_all.empty:
                    mask = (df_all['Description'].str.contains(symbol, na=False, case=False)) | \
                           (df_all['Name'].str.contains(symbol, na=False, case=False))
                    df = df_all[mask]
            except:
                pass

        data = None
        if df is not None and not df.empty:
            raw_row = df.iloc[0].to_dict()
            actual_symbol = raw_row.get('Name', symbol)
            data = process_tvs_row(raw_row, actual_symbol)
            symbol = actual_symbol
            
        if not data or data.get('fScore', 0) == 0 or data.get('eps') is None or data.get('roe') == 0:
            yf_data = fetch_from_yfinance(symbol)
            if yf_data:
                if not data: 
                    data = yf_data
                else:
                    StockService._merge_yf_data(data, yf_data, is_tw)

        if data:
            StockService._enrich_data(data)
            # We don't save history to cache to keep it small, but we could?
            # For now, let's just save metadata.
            StockService._save_to_cache(symbol, data)
            
            # If we are flushing, we might want to return history too for the caller
            history = fetch_history_from_yfinance(symbol, period, interval)
            if history:
                data["history"] = history
            return sanitize_json(data)
        
        return None

    @staticmethod
    def _merge_yf_data(data, yf_data, is_tw):
        yf_price = yf_data.get('price', 0)
        tvs_price = data.get('price', 0)
        
        if yf_price > 0 and tvs_price > 0 and abs(yf_price - tvs_price) / tvs_price > 0.5:
            # Data leak prevention
            return

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

            if k == 'targetPrice':
                curr_p = data.get('price', 1)
                tvs_val = data.get(k, 0)
                is_yf_extreme = (yf_val > 0 and curr_p > 0 and abs(yf_val - curr_p) / curr_p > 0.5)
                is_tvs_extreme = (tvs_val > 0 and curr_p > 0 and abs(tvs_val - curr_p) / curr_p > 0.5)

                if is_yf_extreme:
                    if not is_tvs_extreme and tvs_val > 0:
                        continue 
                    if abs(yf_val - curr_p) / curr_p > 0.8: 
                        continue
                
                if is_tvs_extreme or tvs_val == 0 or is_tw:
                    if not is_yf_extreme:
                        data[k] = yf_val
            
            elif data.get(k) is None or data.get(k) == 0:
                data[k] = yf_val

    @staticmethod
    def _enrich_data(data):
        roe = data.get('roe', 0)
        z_score = data.get('zScore', 0)
        debt = data.get('debtToEquity', 100)
        
        health_label = "普"
        if roe > 15 and z_score > 2.5: health_label = "優"
        elif roe > 8 and z_score > 1.2: health_label = "良"
        elif roe < 0 or z_score < 0.5 or debt > 150: health_label = "差"
        data['healthLabel'] = health_label

        rev_g = data.get('revGrowth', 0)
        f_score = data.get('fScore', 0)
        projection = "持平"
        if rev_g > 20 and f_score >= 6: projection = "高速成長"
        elif rev_g > 5: projection = "溫和成長"
        elif rev_g < -10: projection = "衰退警戒"
        data['growthProjection'] = projection

        price = data.get('price', 1)
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

        atr = data.get('atr', price * 0.02)
        data['prediction'] = {
            "confidence": "中 (68%)" if data.get('fScore', 0) > 4 else "低 (45%)",
            "upper": price + (atr * 2),
            "lower": price - (atr * 2),
            "days": 14
        }

    @staticmethod
    def _save_to_cache(symbol, data):
        conn = get_db_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO stock_cache (symbol, data, updated_at) VALUES (%s, %s, NOW()) ON CONFLICT (symbol) DO UPDATE SET data = EXCLUDED.data, updated_at = NOW()", (symbol, json.dumps(data)))
            conn.commit()
            cur.close()
        finally: return_db_connection(conn)

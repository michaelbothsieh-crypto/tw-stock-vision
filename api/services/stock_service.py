import re
import json
import math
import time
import threading
from api.db import get_db_connection, return_db_connection
from api.constants import TW_STOCK_NAMES
from api.scrapers import fetch_from_yfinance, fetch_history_from_yfinance, sanitize_json, get_field, process_tvs_row, trunc2, calculate_rsi
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tvscreener as tvs
from tvscreener import StockScreener, StockField

# [Optimization] Heavy imports are now at top-level to support unit test mocking.
# MarketRegimeDetector is lazy-initialized on first use.
_MARKET_REGIME = None
_MARKET_REGIME_LOCK = threading.Lock()

def _get_market_regime():
    """Lazy singleton for MarketRegimeDetector."""
    global _MARKET_REGIME
    if _MARKET_REGIME is None:
        with _MARKET_REGIME_LOCK:
            if _MARKET_REGIME is None:
                from api.services.market_regime import MarketRegimeDetector
                _MARKET_REGIME = MarketRegimeDetector()
    return _MARKET_REGIME


# ============================================================
# 記憶體快取層（In-Memory Cache）
# Serverless 友好：模組級變數，在同一容器內持續到冷啟動
# TTL = 300s（5 分鐘），Stale-While-Revalidate 閾値 = 60s
# ============================================================
_MEMORY_CACHE: dict = {}
_CACHE_TTL = 300        # 快取有效期（5 分鐘）
_CACHE_STALE = 60       # 快取即將過期閾値，觸發背景刷新
_CACHE_LOCK = threading.Lock()

def _cache_get(key: str):
    """取得快取，若未命中或已過期回傳 None"""
    entry = _MEMORY_CACHE.get(key)
    if entry and (time.time() - entry['ts']) < _CACHE_TTL:
        return entry['data']
    return None

def _cache_set(key: str, data):
    """寫入快取"""
    with _CACHE_LOCK:
        _MEMORY_CACHE[key] = {'data': data, 'ts': time.time()}

def _cache_is_stale(key: str) -> bool:
    """快取是否即將過期（剩餘時間 < _CACHE_STALE）"""
    entry = _MEMORY_CACHE.get(key)
    if not entry:
        return False
    age = time.time() - entry['ts']
    return age > (_CACHE_TTL - _CACHE_STALE)

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
    def get_market_regime():
        return _get_market_regime().detect_regime()

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
        cache_key = f"trending_{market_param}"

        # ✅ 快取命中：直接回傳，< 1ms
        cached = _cache_get(cache_key)
        if cached is not None:
            # Stale-While-Revalidate：即將過期時在背景刷新
            if _cache_is_stale(cache_key):
                def _bg_refresh():
                    try:
                        fresh = StockService._fetch_trending_from_source(market_param)
                        if fresh:
                            _cache_set(cache_key, fresh)
                            print(f"[Cache] Background refresh done for {cache_key}")
                    except Exception as e:
                        print(f"[Cache] Background refresh error: {e}")
                threading.Thread(target=_bg_refresh, daemon=True).start()
            
            # ✅ Activity-Driven: 利用 API 請求驅動背景批次結算
            def _bg_resolve():
                try:
                    from api.services.performance_tracker import PerformanceTracker
                    resolved = PerformanceTracker.resolve_all_pending()
                    if resolved > 0:
                        print(f"[Activity-Driven] 背景結算 {resolved} 筆預測")
                except Exception as e:
                    print(f"[Activity-Driven] 結算錯誤: {e}")
            threading.Thread(target=_bg_resolve, daemon=True).start()
            
            return cached

        # 快取未命中：嘗試從 DB 獲取 (DB Cache First Strategy)
        t0 = time.time()
        db_results = []
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                # 簡單的 "熱門股" 定義：依成交量排序的最近資料
                # 區分台美股
                market_filter = "symbol ~ '^[0-9]+$'" if market_param == 'TW' else "symbol !~ '^[0-9]+$'"
                cur.execute(f"""
                    SELECT data FROM stock_cache 
                    WHERE {market_filter} 
                    AND updated_at > NOW() - INTERVAL '3 days'
                    ORDER BY (data->>'volume')::numeric DESC
                    LIMIT 15
                """)
                rows = cur.fetchall()
                if rows:
                    db_results = [r[0] for r in rows]
                    print(f"[Timing] DB Cache hit for {market_param}: {len(db_results)} items in {time.time()-t0:.3f}s")
            except Exception as e:
                print(f"[API] DB Cache errors: {e}")
            finally:
                return_db_connection(conn)

        if db_results:
            # 命中 DB 快取：
            # 1. 寫入 Memory Cache (避免短時間重複 DB Query)
            _cache_set(cache_key, db_results)
            
            # 2. 觸發背景刷新 (Stale-While-Revalidate similar logic)
            # 只有當 DB 資料「有點舊」時才刷新？或是每次 Cold Start 都刷新？
            # 為了確保資料新鮮，每次 Cold Start 都觸發背景刷新是安全的
            def _bg_refresh_cold():
                try:
                    t1 = time.time()
                    fresh = StockService._fetch_trending_from_source(market_param)
                    if fresh:
                        _cache_set(cache_key, fresh)
                        print(f"[Cache] Cold-Start Background refresh done for {cache_key} in {time.time()-t1:.3f}s")
                except Exception as e:
                    print(f"[Cache] Cold-Start Background refresh error: {e}")
            threading.Thread(target=_bg_refresh_cold, daemon=True).start()

            print(f"[Timing] Returning DB data for {market_param}. Total time: {time.time()-t0:.3f}s")
            return db_results

        # DB 也沒有資料 (系統初次初始化)：同步取得資料
        print(f"[Timing] Cache & DB Miss. Fetching from Source synchronously...")
        t_src = time.time()
        results = StockService._fetch_trending_from_source(market_param)
        print(f"[Timing] Source fetch done in {time.time()-t_src:.3f}s")
        
        if results:
            _cache_set(cache_key, results)

        # ✅ Activity-Driven: 利用 API 請求驅動背景批次結算
        def _bg_resolve():
            try:
                from api.services.performance_tracker import PerformanceTracker
                resolved = PerformanceTracker.resolve_all_pending()
                if resolved > 0:
                    print(f"[Activity-Driven] 背景結算 {resolved} 筆預測")
            except Exception as e:
                print(f"[Activity-Driven] 結算錯誤: {e}")
        threading.Thread(target=_bg_resolve, daemon=True).start()

        return results

    @staticmethod
    def _fetch_trending_from_source(market_param):
        """從 tvscreener 取得 trending 資料（原有邏輯，抽出為獨立方法）"""
        t_start = time.time()
        market_param = market_param.upper()
        is_tw = (market_param == 'TW')
        import tvscreener as tvs
        from tvscreener import StockScreener, StockField
        results = []
        try:
            ss = StockScreener()
            # 設定市場
            ss.set_markets(tvs.Market.TAIWAN if is_tw else tvs.Market.AMERICA)
            
            # 增加關鍵欄位選擇
            ss.select(StockField.NAME, StockField.DESCRIPTION, StockField.PRICE, 
                      StockField.CHANGE, StockField.CHANGE_PERCENT, StockField.VOLUME,
                      StockField.TECHNICAL_RATING, StockField.PIOTROSKI_F_SCORE_TTM,
                      StockField.MARKET_CAPITALIZATION, StockField.SECTOR, StockField.EXCHANGE)
            
            # 篩選邏輯：
            # 1. 技術評級 > 0.3 (中性偏買)
            # 2. F-Score > 4 (財務品質良好)
            # 3. 成交量 > 指定門檻 (確保流動性)
            min_vol = 1000000 if is_tw else 2000000
            
            # 使用 tvscreener 的過濾法 (如果 API 支援), 否則在本地過濾 DataFrame
            df = ss.get()
            
            if df is not None and not df.empty:
                # 本地過濾以確保數據質量
                filtered_df = df.copy()
                
                # 安全轉換數值
                def to_num(ser): return ser.apply(lambda x: float(x) if x is not None and not isinstance(x, str) else 0)
                
                v_col = 'Volume' if 'Volume' in df.columns else StockField.VOLUME.label
                t_col = 'Technical Rating' if 'Technical Rating' in df.columns else StockField.TECHNICAL_RATING.label
                f_col = 'Piotroski F-Score (TTM)' if 'Piotroski F-Score (TTM)' in df.columns else StockField.PIOTROSKI_F_SCORE_TTM.label
                
                # 過濾量、評級與財務品質 (F-Score)
                # 為確保結果不為空，F-Score 門檻設為 3
                mask = (to_num(filtered_df[v_col]) > min_vol) & (to_num(filtered_df[t_col]) > 0.2)
                final_df = filtered_df[mask].sort_values(by=[v_col], ascending=False).head(15)
                
                # [ 效能優化 ] 使用 ThreadPoolExecutor 並行處理指標補全與快取同步
                stock_list = []
                for _, row_raw in final_df.iterrows():
                    row_dict = row_raw.to_dict()
                    symbol = row_dict.get('Name', '')
                    if not symbol: continue
                    
                    is_symbol_tw = bool(re.match(r'^[0-9]+$', symbol))
                    if is_tw and not is_symbol_tw: continue
                    if not is_tw and is_symbol_tw: continue
                    stock_list.append((symbol, row_dict))

                # [Optimization] Pre-compute shared values ONCE, outside per-stock loop
                try:
                    regime = _get_market_regime().detect_regime()
                except Exception:
                    regime = "sideways"

                strategy_params = {}
                try:
                    config_path = Path(__file__).parent.parent / "strategy_config.json"
                    if config_path.exists():
                        with open(config_path, "r", encoding="utf-8") as f:
                            full_config = json.load(f)
                            strategy_params = full_config.get("strategies", {}).get("growth_value", {})
                except Exception:
                    pass

                # [Optimization] 列表頁移除 yfinance fallback，只用 TVScreener 資料
                # 避免 Vercel Timeout (10s limit)
                def enrich_fast(symbol, row_dict):
                    try:
                        data = process_tvs_row(row_dict, symbol)
                        StockService._enrich_data(data)
                        StockService._save_to_cache(symbol, data)
                        return data
                    except Exception as e:
                        print(f"Error enriching {symbol}: {e}")
                        return None

                # [Performance] 直接處理，不再使用 ThreadPool 等待 I/O
                # 因為移除了 I/O (yfinance)，這些都是純記憶體操作，速度極快
                for s, r in stock_list:
                    res = enrich_fast(s, r)
                    if res: results.append(res)
                
                # 再次排序並僅保留前 10
                results.sort(key=lambda x: x.get('volume', 0), reverse=True)
                return results[:10]
            
            # 備選方案：當 API 抓取失敗時，從 DB 快取載入舊資料，確保啟動不報錯
            if not results:
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        market_filter = "symbol ~ '^[0-9]+$'" if is_tw else "symbol ~ '^[A-Z]+$'"
                        cur.execute(f"""
                            SELECT data FROM stock_cache 
                            WHERE {market_filter} 
                            AND updated_at > NOW() - INTERVAL '24 hours'
                            ORDER BY (data->>'fScore')::numeric DESC, (data->>'technicalRating')::numeric DESC
                            LIMIT 15
                        """)
                        results = [r[0] for r in cur.fetchall()]
                        cur.close()
                    finally:
                        return_db_connection(conn)
                    
        except Exception as e:
            print(f"Error in dynamic trending: {e}")
            return []
            
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
            cur.execute("SELECT data, updated_at FROM stock_cache WHERE symbol = %s", (symbol,))
            row = cur.fetchone()
            cur.close()
            
            if row:
                cached_data = dict(row[0]) if isinstance(row[0], dict) else {}
                cache_updated_at = row[1] if len(row) > 1 else None
                
                # [Optimization] Inject cached_at for clients to determine freshness
                if cache_updated_at:
                    cached_data['_cached_at'] = cache_updated_at.isoformat()
                
                # [Fix] History TTL: re-fetch if older than 24 hours
                from datetime import datetime, timezone
                history_stale = True
                if cache_updated_at:
                    try:
                        if cache_updated_at.tzinfo is None:
                            cache_updated_at = cache_updated_at.replace(tzinfo=timezone.utc)
                        age_hours = (datetime.now(timezone.utc) - cache_updated_at).total_seconds() / 3600
                        history_stale = (age_hours > 24)
                    except Exception:
                        history_stale = True

                history_key = f"history_{period}_{interval}"

                if cached_data.get(history_key) and not history_stale:
                    cached_data["history"] = cached_data[history_key]
                    return sanitize_json(cached_data)

                # Fetch history if missing or stale
                try:
                    history = fetch_history_from_yfinance(symbol, period=period, interval=interval)
                    if history:
                        cached_data[history_key] = history
                        cached_data["history"] = history
                        StockService._save_to_cache(symbol, cached_data)
                    else:
                        cached_data["history"] = []
                except Exception as e:
                    print(f"Non-critical: History fetch failed for {symbol}: {e}")
                    cached_data["history"] = []
                
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
            
            # ✅ AI 進化閃環：取得個股詳情時，順便檢查是否可結算預測
            try:
                from api.services.performance_tracker import PerformanceTracker
                curr_p = float(data.get('price') or 0)
                if curr_p > 0:
                    PerformanceTracker.check_and_resolve_pending(symbol, curr_p)
            except Exception as e:
                print(f"[PerformanceTracker] check_and_resolve_pending error for {symbol}: {e}")
            
            # If we are flushing, we might want to return history too for the caller
            history = fetch_history_from_yfinance(symbol, period, interval)
            history_key = f"history_{period}_{interval}"
            if history:
                data[history_key] = history
                data["history"] = history
                # Save the flushed data + history to cache to avoid immediate refetch
                StockService._save_to_cache(symbol, data)
            else:
                data["history"] = []
                
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

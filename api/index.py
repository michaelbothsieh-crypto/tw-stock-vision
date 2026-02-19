from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re
import threading
from pathlib import Path

# Modular Imports
from api.db import get_db_connection, return_db_connection, init_db
from api.constants import TW_STOCK_NAMES
from api.services.stock_service import StockService
from functools import lru_cache

# Non-blocking DB Initialization (Lazy-loaded inside db.py get_db_connection)
# Legacy: threading.Thread(target=init_db, daemon=True).start()

# Initialize Stock Names (Empty start, lazy load if needed)
# Legacy code removed: No longer fetching full list on startup.
# Usage updates handled by scripts/sync_names.py and DB.
TW_STOCK_NAMES.update({}) 


# [Optimization] Removed pre_warm_cache on startup to ensure instant launch.
# SWR mechanism in StockService handles background refreshes on first request.
# threading.Thread(target=pre_warm_cache, daemon=True).start()

@lru_cache(maxsize=1)
def load_strategy_config():
    try:
        config_path = Path(__file__).parent / "strategy_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[API] Error loading strategy config: {e}")
    return {}

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
                    price = StockService.get_current_price(symbol) or 0
                
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
            
            elif action == 'get_quote':
                symbol = data.get('symbol')
                from api.scrapers import fetch_realtime_quote
                quote = fetch_realtime_quote(symbol)
                if quote:
                    self.wfile.write(json.dumps({"status": "success", "quote": quote}).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({"error": "Failed to fetch quote"}).encode('utf-8'))

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

            elif action == 'trigger_evolution':
                # ✅ 新增：手動觸發每日反思（build-ai-agent-system Step 4: Evaluate and iterate）
                from api.services.reflection_engine import ReflectionEngine
                actual_performance = data.get('actual_performance', {'avg_return': 0})
                predicted_stocks = data.get('predicted_stocks', [])
                reflections = ReflectionEngine.run_daily_reflection(predicted_stocks, actual_performance)
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'reflections': reflections,
                    'message': f'Evolution triggered: {len(reflections)} strategies updated'
                }).encode('utf-8'))

            # ✅ 修復：cur.close() 移至 finally，確保不被 early return 跳過
            cur.close()
            return_db_connection(conn)
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))



    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            q = parse_qs(parsed.query)
            if 'leaderboard' in q or '/leaderboard' in parsed.path: 
                data = StockService.get_leaderboard()
                self._set_headers()
                self.wfile.write(json.dumps(data, default=str).encode('utf-8'))
            elif 'trending' in q or '/market/trending' in parsed.path: 
                market = q.get('market', ['TW'])[0]
                data = StockService.get_market_trending(market)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            elif 'symbol' in q: 
                symbol = q['symbol'][0]
                period = q.get('period', ['1y'])[0]
                interval = q.get('interval', ['1d'])[0]
                # flush = q.get('flush', ['false'])[0].lower() == 'true'
                
                from api.services.agent_tools import StockAgentTools
                data = StockAgentTools.fetch_comprehensive_data(symbol, period, interval)
                
                self._set_headers()
                if data:
                    self.wfile.write(json.dumps(data).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({"error": "Unable to fetch data", "symbol": symbol}).encode('utf-8'))
            elif parsed.path.endswith('/health'):
                self._set_headers()
                from api.services.evolution_manager import EvolutionManager
                EvolutionManager.log_anomaly("HEALTH_CHECK", "API health endpoint accessed")
                self.wfile.write(json.dumps({"status": "ok", "evolution": "active"}).encode('utf-8'))
            elif parsed.path.endswith('/evolution'):
                self._set_headers()
                from api.services.reflection_engine import ReflectionEngine
                from api.services.evolution_manager import EvolutionManager
                from api.services.performance_tracker import PerformanceTracker
                
                state = ReflectionEngine.load_state()
                
                # ✅ 完整進化狀態：策略狀態 + 異常統計 + 預測準確率 + 市場狀態 + 策略變數
                state['anomaly_summary'] = EvolutionManager.get_anomaly_summary()
                state['performance_tracking'] = PerformanceTracker.get_summary()
                state['market_regime'] = StockService.get_market_regime()
                state['strategy_config'] = load_strategy_config()
                
                self.wfile.write(json.dumps(state).encode('utf-8'))
            else:
                self._set_headers()
                self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))
        except Exception as e:
            import sys
            import traceback
            from api.services.evolution_manager import EvolutionManager
            EvolutionManager.log_anomaly("CRITICAL_ERROR", str(e), {"trace": traceback.format_exc()})
            print(f"CRITICAL ERROR in do_GET: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Internal Server Error", "details": str(e)}).encode('utf-8'))

if __name__ == '__main__':
    from http.server import HTTPServer
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    print(f"Starting local dev server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

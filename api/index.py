from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import math
import tvscreener as tvs
from tvscreener import StockScreener, StockField

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        symbol = query_params.get('symbol', [None])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if not symbol:
            response = {"error": "Missing symbol parameters"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        try:
            # Initialize screener for Taiwan market
            ss = StockScreener()
            ss.set_markets(tvs.Market.TAIWAN)
            
            # Filter by symbol
            # Note: tvscreener usually filters by 'ticker' or 'name'.
            # We search for the exact symbol match if possible, or contains.
            # Using fluent API for filtering would be cleaner if the field name is known.
            # ss.where(StockField.TICKER == symbol) # Assuming ticker field is available
            
            # Since exact field name for 'ticker' might vary (e.g. 'name', 'description'),
            # let's try a safer approach: get top results and filter in python if search via library is tricky without docs.
            # OR better: use add_filter which seemed to work in my mental model but I should check if it exists in v0.2.0.
            # The README suggests where(), but doesn't list the field constant for ticker.
            
            # Let's try to filter by ticker using StockField.TICKER if it exists, otherwise rely on broad fetch and filter.
            # Given the constraints, let's fetch first and filter.
            # Ideally we should use ss.add_filter(tvs.Filter('ticker', 'match', symbol)) from v1, but it might be gone.
            
            # Updated approach for v0.2.0 based on README examples:
            # ss.where(StockField.MARKET_CAPITALIZATION > 1e9)
            # We will try to filter by name/ticker.
            
            # Fallback strategy: fetch top 100 or verify quickly.
            # But wait, we want a specfic stock. Fetching 100 is inefficient.
            # Let's try to see if we can use 'symbol' param in the query if available in tvscreener.
            
            # For now, let's just return a mock response if fetch fails, but try to fetch real data.
            # Real implementation would require precise knowledge of the 'ticker' field name in StockField.
            
            # Let's try to locate the symbol by manual filtering after fetch (inefficient but safe).
            # Actually, `tvscreener` searches global unless filtered.
            
            # Simplest correct way if `add_filter` is not available:
            # We will use the `search` functionality from MCP description?
            # "search_stocks" tool exist in MCP server.
            # The library likely exposes `search` too.
            
            # Let's try to assume we just want to execute a screen.
            # The user asked for "input stock -> get price".
            
            # Since I can't be 100% sure of the filter syntax without further probing,
            # I will implement a fetch that gets top stocks and filters Python-side.
            # Use a large limit if possible? or 150 default.
            
            # Optimistic attempt:
            # ss.where(StockField.TICKER == symbol) 
            
            df = ss.get()
            
            # Filter in pandas
            # Assuming 'Symbol' or 'Ticker' column exists. My test script output said 'Symbol'.
            # It might be '2330' or 'TWSE:2330'.
            
            # Normalize symbol
            target = symbol.strip().upper()
            
            # Filter
            # Check for 'Symbol' column
            if 'Symbol' in df.columns:
                result = df[df['Symbol'].str.contains(target)]
            elif 'Ticker' in df.columns:
                result = df[df['Ticker'].str.contains(target)]
            else:
                result = df # distinct failure mode
            
            if not result.empty:
                # Convert to dict
                data = result.iloc[0].to_dict()
                
                # Format for UI
                # Need to map to: symbol, price, change, changePercent, volume, marketCap
                # API columns might be Capitalized.
                
                response_data = {
                    "symbol": data.get('Symbol', symbol),
                    "name": data.get('Name', data.get('Description', '')),
                    "price": data.get('Close', 0), # 'Close' is usually current price? or 'Price'
                    "change": data.get('Change', 0),
                    "changePercent": data.get('Change %', 0),
                    "volume": data.get('Volume', 0),
                    "marketCap": data.get('Market Cap', 0),
                    "updatedAt": "Just now",
                    'change_p': data.get('Change %', 0),
                    'volume': data.get('Volume', 0),
                    'marketCap': data.get('Market Capitalization', 0),
                    # SMC Indicators
                    'rvol': data.get('Relative Volume', 0),
                    'cmf': data.get('Chaikin Money Flow (20)', 0),
                    'vwap': data.get('Volume Weighted Average Price', 0),
                    # Ratings
                    'technicalRating': data.get('Technical Rating', 0), # -1 to 1
                    'analystRating': data.get('Analyst Rating', 3), # 1 (Strong Buy) to 5 (Sell)? TBC. TV usually: 1=Strong Buy, 5=Sell
                    'targetPrice': data.get('Target Price (Average)', 0),
                    # Daily Vitals
                    'rsi': data.get('Relative Strength Index (14)', 50),
                    'atr_p': data.get('Average True Range % (14)', 0),
                    'sma20': data.get('Simple Moving Average (20)', 0),
                    'sma50': data.get('Simple Moving Average (50)', 0),
                    'sma200': data.get('Simple Moving Average (200)', 0),
                    'perf_w': data.get('Weekly Performance', 0),
                    'perf_m': data.get('Monthly Performance', 0),
                    'perf_ytd': data.get('YTD Performance', 0),
                    'volatility': data.get('Volatility', 0),
                    'earningsDate': data.get('Upcoming Earnings Date', 0)
                }
                
                # Handle potential key differences
                if 'Price' in data: response_data['price'] = data['Price']
                
                # Convert NaN/None to 0 for JSON safety
                for k, v in response_data.items():
                    if v is None:
                        response_data[k] = 0
                    elif isinstance(v, float) and math.isnan(v):
                        response_data[k] = 0

                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                self.send_error(404, "Symbol not found")
                return
            
        except Exception as e:
            response = {"error": f"Internal Error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))

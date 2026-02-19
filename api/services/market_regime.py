from datetime import datetime, timedelta

# [Optimization] yfinance and numpy are lazy-loaded in detect_regime()

class MarketRegimeDetector:
    def __init__(self, index_symbol="^TWII"):
        """
        Initialize with a market index symbol.
        Default is Taiwan Weighted Index (^TWII).
        """
        self.index_symbol = index_symbol
        self.current_regime = "sideways"
        self.last_update = None

    def detect_regime(self, lookback_days=30):
        """
        Detect if the market is in Bull, Bear, or Sideways regime.
        Based on simple return over the lookback period.
        """
        # If we checked recently (e.g. within 1 hour), return cached
        if self.last_update and (datetime.now() - self.last_update).seconds < 3600:
            return self.current_regime

        try:
            import yfinance as yf
            # Fetch history
            ticker = yf.Ticker(self.index_symbol)
            # Fetch slightly more than lookback to ensure we have endpoints
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 10)
            
            history = ticker.history(start=start_date, end=end_date)
            
            if len(history) < 2:
                return "sideways" # Not enough data

            # Get price lookback_days ago (or closest)
            # We want the change from (Now - Lookback) to Now
            
            # Simple approach: Linear Regression Slope or just Return?
            # Let's use Return for simplicity as defined in plan: "根據最近 30 日大盤漲跌幅計算"
            
            current_price = history['Close'].iloc[-1]
            past_price = history['Close'].iloc[0] # This is start_date approx
            
            # Refine: Find the row closest to exactly lookback_days ago
            target_date = end_date - timedelta(days=lookback_days)
            # Find index closest to target_date
            # Since index is DatetimeIndex, we can use get_loc with method='nearest' if available
            # Or just take the first element if we fetched correctly.
            # Let's use the percentage change of the window.
            
            # Return = (Last - First) / First
            market_return = (current_price - past_price) / past_price

            # Define thresholds (Move to config later if needed, but for now defaults)
            BULL_THRESHOLD = 0.05  # > 5% gain
            BEAR_THRESHOLD = -0.05 # > 5% loss
            
            if market_return > BULL_THRESHOLD:
                self.current_regime = "bull"
            elif market_return < BEAR_THRESHOLD:
                self.current_regime = "bear"
            else:
                self.current_regime = "sideways"
                
            self.last_update = datetime.now()
            print(f"[MarketRegime] Index: {self.index_symbol}, Return: {market_return:.2%}, Regime: {self.current_regime}")
            return self.current_regime

        except Exception as e:
            print(f"[MarketRegime] Error detecting regime: {e}")
            return "sideways" # Default fallback

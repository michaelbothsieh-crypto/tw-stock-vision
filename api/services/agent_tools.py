import json
from api.services.stock_service import StockService
from api.services.evolution_manager import EvolutionManager

class StockAgentTools:
    """
    提供給 AI Agent 使用的台股工具集
    封裝了抓取、自癒與分析邏輯。
    """

    @staticmethod
    def fetch_comprehensive_data(symbol: str, period: str = "1y", interval: str = "1d"):
        """
        獲取完整的股票數據。若發現關鍵數據缺失，會自動紀錄並觸發自進化流程。
        """
        # [ 進化邏輯 ] 根據歷史記憶決定初始來源
        preferred_source = EvolutionManager.suggest_source(symbol)

        # 第一步：嘗試獲取基本數據
        data = StockService.get_stock_details(symbol, period, interval)

        # ✅ 修復：只有 None 才算缺失，0 是合法值（例如 F-Score=0 代表財務差，不是資料缺失）
        required_fields = ["fScore", "eps", "zScore", "targetPrice"]
        missing = [f for f in required_fields if not data or data.get(f) is None]

        if missing:
            # [Optimization] Check if data is fresh (< 24h). If so, do not re-flush.
            # This prevents infinite loops for stocks that genuinely lack data (e.g. ETFs).
            is_recent = False
            if data and data.get('_cached_at'):
                from datetime import datetime, timezone, timedelta
                try:
                    cached_at = datetime.fromisoformat(data.get('_cached_at'))
                    if cached_at.tzinfo is None:
                        cached_at = cached_at.replace(tzinfo=timezone.utc)
                    
                    # If cached within last 24 hours, consider it "tried recently"
                    if (datetime.now(timezone.utc) - cached_at) < timedelta(hours=24):
                        is_recent = True
                except:
                    pass

            if not is_recent:
                EvolutionManager.log_anomaly(
                    "DATA_MISSING",
                    f"股票 {symbol} 缺失關鍵欄位: {missing} (來源: {preferred_source})",
                    {"symbol": symbol, "missing_fields": missing, "source": preferred_source}
                )

                # [ 自癒閉環 ] 若首選來源失敗且非 yfinance，嘗試切換
                if preferred_source != "yfinance":
                    print(f"[Evolution] Detecting missing data for {symbol}, triggering self-healing via yfinance...")
                    data = StockService.get_stock_details(symbol, period, interval, flush=True)
            else:
                # Log but don't flush
                # print(f"[AgentTools] Missing {missing} for {symbol} but cache is fresh (<24h). Skipping flush.")
                pass

        return data

    @staticmethod
    def get_market_sentiment(market: str = "TW"):
        """
        獲取市場趨勢情緒。
        """
        return StockService.get_market_trending(market)

    @staticmethod
    def record_evolution_feedback(feedback: str, symbol: str = None):
        """
        紀錄來自用戶或 Agent 的進化反饋。
        """
        EvolutionManager.log_anomaly("USER_FEEDBACK", feedback, {"symbol": symbol})
        return {"status": "success", "message": "Feedback recorded for evolution cycle"}

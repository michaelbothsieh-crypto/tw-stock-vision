"""
PerformanceTracker — AI 自我進化閉環的「觀察層」

職責：
1. 記錄策略預測快照（預測時的評分）
2. N 天後記錄實際報酬率
3. 計算策略準確率，供 ReflectionEngine 使用
4. 達到觸發條件時自動呼叫 ReflectionEngine

設計原則：
- 使用 DB 持久化（stock_cache 表的 metadata 欄位），不依賴記憶體
- 無外部依賴，可在 Vercel serverless 環境運行
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from api.db import get_db_connection, return_db_connection

# 進化觸發條件
EVOLUTION_TRIGGERS = {
    "accuracy_drop_threshold": 0.40,   # 準確率低於 40% 時觸發進化
    "min_sample_size": 5,              # 至少 5 筆樣本才計算準確率
    "lookback_days": 14,               # 回顧 14 天的預測記錄
}

# 持久化路徑（Serverless 友好：使用 /tmp）
_TRACKER_FILE = Path("/tmp/performance_tracker.json")


class PerformanceTracker:
    """
    AI 進化閉環的觀察層。
    追蹤預測 → 實際表現，提供準確率數據給 ReflectionEngine。
    """

    @staticmethod
    def _load() -> dict:
        """載入追蹤記錄（優先從 /tmp，Vercel 環境可用）"""
        try:
            if _TRACKER_FILE.exists():
                return json.loads(_TRACKER_FILE.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"[PerformanceTracker] Load error: {e}")
        return {"predictions": [], "actuals": []}

    @staticmethod
    def _save(data: dict):
        """儲存追蹤記錄"""
        try:
            _TRACKER_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"[PerformanceTracker] Save error: {e}")

    @staticmethod
    @staticmethod
    def record_prediction(symbol: str, strategy_id: str, predicted_score: float, initial_price: float, details: dict = None):
        """
        記錄預測快照。
        在 get_market_trending 推薦股票時呼叫。

        Args:
            symbol: 股票代號（如 "2330"）
            strategy_id: 策略 ID（如 "growth_value"）
            predicted_score: 預測評分（0-10）
            initial_price: 預測時的股價（用於計算報酬率）
            details: 額外資訊（如 market regime, RSI 等）
        """
        data = PerformanceTracker._load()
        data["predictions"].append({
            "symbol": symbol,
            "strategy_id": strategy_id,
            "predicted_score": predicted_score,
            "initial_price": initial_price,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "resolved": False,
        })
        # 只保留最近 30 天的記錄
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        data["predictions"] = [p for p in data["predictions"] if p["timestamp"] > cutoff]
        PerformanceTracker._save(data)

    @staticmethod
    def check_and_resolve_pending(symbol: str, current_price: float):
        """
        檢查是否有待解決的預測，若持有時間足夠則自動結算。
        由 stock_service 在取得新報價時呼叫。
        """
        data = PerformanceTracker._load()
        updated = False
        min_hold_hours = 24  # 至少持有 24 小時才結算 (測試時可縮短)

        for pred in data["predictions"]:
            if pred["symbol"] == symbol and not pred.get("resolved"):
                pred_time = datetime.fromisoformat(pred["timestamp"])
                hours_passed = (datetime.now() - pred_time).total_seconds() / 3600

                if hours_passed >= min_hold_hours:
                    initial = pred.get("initial_price")
                    if initial and initial > 0:
                        reward_pct = ((current_price - initial) / initial) * 100
                        pred["resolved"] = True
                        pred["actual_return_pct"] = round(reward_pct, 2)
                        pred["resolved_at"] = datetime.now().isoformat()
                        pred["final_price"] = current_price
                        updated = True
        
        if updated:
            PerformanceTracker._save(data)
            PerformanceTracker._check_and_trigger_evolution(data)

    @staticmethod
    def record_actual(symbol: str, actual_return_pct: float, days_held: int = 5):
        """
        記錄實際報酬率。
        可由排程任務或 trigger_evolution API 呼叫。

        Args:
            symbol: 股票代號
            actual_return_pct: 實際報酬率（%，如 2.5 代表 +2.5%）
            days_held: 持有天數
        """
        data = PerformanceTracker._load()

        # 找到對應的預測記錄並標記為已解決
        for pred in data["predictions"]:
            if pred["symbol"] == symbol and not pred["resolved"]:
                pred["resolved"] = True
                pred["actual_return_pct"] = actual_return_pct
                pred["days_held"] = days_held
                pred["resolved_at"] = datetime.now().isoformat()
                break

        PerformanceTracker._save(data)

        # 檢查是否需要觸發進化
        PerformanceTracker._check_and_trigger_evolution(data)

    @staticmethod
    def calculate_accuracy(strategy_id: str = None, lookback_days: int = None) -> dict:
        """
        計算策略準確率。
        「準確」定義：預測評分 > 5 且實際報酬率 > 0（或反之）。

        Returns:
            {
                "accuracy": 0.65,      # 準確率 65%
                "sample_size": 20,     # 樣本數
                "avg_return": 1.2,     # 平均實際報酬率 %
                "strategy_id": "..."
            }
        """
        lookback_days = lookback_days or EVOLUTION_TRIGGERS["lookback_days"]
        data = PerformanceTracker._load()
        cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()

        resolved = [
            p for p in data["predictions"]
            if p.get("resolved")
            and p["timestamp"] > cutoff
            and (strategy_id is None or p.get("strategy_id") == strategy_id)
        ]

        if len(resolved) < EVOLUTION_TRIGGERS["min_sample_size"]:
            return {
                "accuracy": None,
                "sample_size": len(resolved),
                "avg_return": None,
                "strategy_id": strategy_id,
                "message": f"樣本不足（需要 {EVOLUTION_TRIGGERS['min_sample_size']} 筆，目前 {len(resolved)} 筆）"
            }

        # 準確率計算：預測方向與實際方向一致
        correct = sum(
            1 for p in resolved
            if (p["predicted_score"] > 5) == (p["actual_return_pct"] > 0)
        )
        avg_return = sum(p["actual_return_pct"] for p in resolved) / len(resolved)

        return {
            "accuracy": round(correct / len(resolved), 3),
            "sample_size": len(resolved),
            "avg_return": round(avg_return, 2),
            "strategy_id": strategy_id,
        }

    @staticmethod
    def _check_and_trigger_evolution(data: dict):
        """
        檢查是否達到進化觸發條件，若是則自動呼叫 ReflectionEngine。
        """
        stats = PerformanceTracker.calculate_accuracy()

        if stats["accuracy"] is None:
            return  # 樣本不足，不觸發

        threshold = EVOLUTION_TRIGGERS["accuracy_drop_threshold"]
        if stats["accuracy"] < threshold:
            print(f"[PerformanceTracker] 準確率 {stats['accuracy']:.1%} < {threshold:.0%}，自動觸發進化！")
            try:
                from api.services.reflection_engine import ReflectionEngine
                actual_perf = {"avg_return": stats["avg_return"] / 100}  # 轉換為小數
                reflections = ReflectionEngine.run_daily_reflection([], actual_perf)
                print(f"[PerformanceTracker] 進化完成：{reflections}")
            except Exception as e:
                print(f"[PerformanceTracker] 自動進化觸發失敗：{e}")

    @staticmethod
    def get_summary() -> dict:
        """取得追蹤摘要，供 /evolution API 端點使用"""
        data = PerformanceTracker._load()
        total = len(data["predictions"])
        resolved = [p for p in data["predictions"] if p.get("resolved")]
        pending = total - len(resolved)

        return {
            "total_predictions": total,
            "resolved": len(resolved),
            "pending": pending,
            "accuracy_stats": PerformanceTracker.calculate_accuracy(),
        }

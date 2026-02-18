import json
import os
from datetime import datetime
from pathlib import Path

# 動態解析路徑，相容本地開發與 Vercel serverless 環境
_BASE_DIR = Path(__file__).parent.parent

class EvolutionManager:
    """
    TwStockVision 自進化管理器
    負責紀錄數據異常、邊界錯誤，並提供系統進化的建議。
    """
    LOG_FILE = _BASE_DIR / "evolution.log"
    RULES_FILE = _BASE_DIR / "evolution_rules.json"

    @staticmethod
    def log_anomaly(category, message, metadata=None):
        """紀錄異常狀況，作為未來進化的依據"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "message": message,
            "metadata": metadata or {}
        }

        try:
            EvolutionManager.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(EvolutionManager.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            print(f"[Evolution] Recorded {category}: {message}")
        except OSError as e:
            print(f"[Evolution] Error writing log: {e}")

    @staticmethod
    def get_evolution_rules():
        """取得動態進化規則"""
        if not EvolutionManager.RULES_FILE.exists():
            return {
                "strict_validation": True,
                "auto_healing_enabled": True,
                "metrics_boundary": {
                    "fScore": [0, 9],
                    "targetPrice": [0, 5000]
                }
            }

        try:
            with open(EvolutionManager.RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[Evolution] Error reading rules: {e}")
            return {}

    @staticmethod
    def suggest_source(symbol):
        """根據歷史紀錄推薦最優抓取來源 (自進化核心邏輯)"""
        if not EvolutionManager.LOG_FILE.exists():
            return "tv_screener"

        try:
            with open(EvolutionManager.LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        meta = entry.get("metadata", {})
                        if meta.get("symbol") == symbol and entry.get("category") == "DATA_MISSING":
                            return "yfinance"
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            print(f"[Evolution] Error reading log for suggest_source: {e}")

        return "tv_screener"

    @staticmethod
    def get_anomaly_summary():
        """取得異常紀錄統計摘要，供 /evolution 端點使用"""
        summary = {}
        if not EvolutionManager.LOG_FILE.exists():
            return summary

        try:
            with open(EvolutionManager.LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        cat = entry.get("category", "UNKNOWN")
                        summary[cat] = summary.get(cat, 0) + 1
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            print(f"[Evolution] Error reading log for summary: {e}")

        return summary

    @staticmethod
    def recommend_action(anomaly_log):
        """根據紀錄推薦下一步行動"""
        category = anomaly_log.get("category")
        if category == "DATA_MISSING":
            return "建議檢查 TVScreener 欄位映射或強制啟用 yfinance 補償邏輯"
        elif category == "TIMEOUT":
            return "建議增加 API Timeout 閾值或使用非阻塞非同步抓取"
        return "觀察中"


if __name__ == "__main__":
    # 測試用途
    EvolutionManager.log_anomaly("SYSTEM_START", "Evolution Manager Initialized")
    print(EvolutionManager.get_evolution_rules())
    print(EvolutionManager.get_anomaly_summary())

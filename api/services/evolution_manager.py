import json
import os
from datetime import datetime

class EvolutionManager:
    """
    TwStockVision 自進化管理器
    負責紀錄數據異常、邊界錯誤，並提供系統進化的建議。
    """
    LOG_FILE = "api/evolution.log"
    RULES_FILE = "api/evolution_rules.json"

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
            # 確保目錄存在
            os.makedirs(os.path.dirname(EvolutionManager.LOG_FILE), exist_ok=True)
            
            with open(EvolutionManager.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            print(f"[Evolution] Recorded {category}: {message}")
        except Exception as e:
            print(f"[Evolution] Error writing log: {e}")

    @staticmethod
    def get_evolution_rules():
        """取得動態進化規則"""
        if not os.path.exists(EvolutionManager.RULES_FILE):
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
        except:
            return {}

    @staticmethod
    def suggest_source(symbol):
        """根據歷史紀錄推薦最優抓取來源 (自進化核心邏輯)"""
        # 簡單邏輯：若該 symbol 在 log 中有 DATA_MISSING 紀錄，推薦切換至 yfinance
        if not os.path.exists(EvolutionManager.LOG_FILE):
            return "tv_screener"
            
        with open(EvolutionManager.LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("metadata", {}).get("symbol") == symbol and entry.get("category") == "DATA_MISSING":
                        return "yfinance"
                except:
                    continue
        return "tv_screener"

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

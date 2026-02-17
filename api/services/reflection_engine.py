import json
import os
from datetime import datetime
from api.services.evolution_manager import EvolutionManager

class ReflectionEngine:
    """
    Self-Evolving Alpha Lab 核心反射引擎
    負責比對表現並自動進化策略參數。
    """
    STATE_FILE = "api/evolution_state.json"

    @staticmethod
    def load_state():
        if not os.path.exists(ReflectionEngine.STATE_FILE):
            return {}
        with open(ReflectionEngine.STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_state(state):
        with open(ReflectionEngine.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    @staticmethod
    def run_daily_reflection(predicted_stocks, actual_performance):
        """
        執行每日反思與權重微調核心邏輯
        :param predicted_stocks: 昨日推薦清單與預期分數
        :param actual_performance: 今日實測漲跌幅
        """
        state = ReflectionEngine.load_state()
        history_entry = {
            "date": datetime.now().isoformat(),
            "performance": actual_performance,
            "reflections": []
        }

        # 簡單梯度調整範例：若 F-Score 高但股價跌，調降權重
        # 這只是原型邏輯，未來會整合更多歸因分析
        learning_rate = state.get("mutation_config", {}).get("learning_rate", 0.01)
        
        # 遍歷目前策略進行演化
        for s_id, strategy in state.get("strategies", {}).items():
            current_weights = strategy["weights"]
            new_weights = current_weights.copy()
            
            # [自進化邏輯] 這裡預留給複雜的歸因算法
            # 此處模擬：若整體表現低於預期，則進行探索性微調
            if actual_performance.get("avg_return", 0) < 0:
                EvolutionManager.log_anomaly("EVOLUTION_TRIGGER", f"策略 {s_id} 表現不佳，觸發微調")
                # 簡單地將權重向營收成長偏移 (假設近期市場看重成長)
                new_weights["eps_growth"] = round(new_weights.get("eps_growth", 0) + learning_rate, 3)
                new_weights["fScore"] = round(new_weights.get("fScore", 0) - learning_rate, 3)
            
            strategy["weights"] = new_weights
            history_entry["reflections"].append(f"Adjusted {s_id} weights based on market response.")

        strategy["performance_history"].append(history_entry)
        ReflectionEngine.save_state(state)
        
        return history_entry["reflections"]

if __name__ == "__main__":
    # 測試模擬執行
    engine = ReflectionEngine()
    results = engine.run_daily_reflection(
        predicted_stocks=[], 
        actual_performance={"avg_return": -0.02}
    )
    print(results)

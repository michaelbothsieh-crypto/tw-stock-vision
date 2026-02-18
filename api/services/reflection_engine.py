import json
import os
from datetime import datetime
from pathlib import Path
from api.services.evolution_manager import EvolutionManager

class ReflectionEngine:
    """
    Self-Evolving Alpha Lab 核心反射引擎
    負責比對表現並自動進化策略參數。
    """
    STATE_FILE = Path(__file__).parent.parent / "evolution_state.json"
    MAX_HISTORY = 30  # Rolling window：最多保留 30 筆歷史

    @staticmethod
    def load_state():
        if not ReflectionEngine.STATE_FILE.exists():
            return {}
        try:
            with open(ReflectionEngine.STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ReflectionEngine] Failed to load state: {e}")
            return {}

    @staticmethod
    def load_config():
        """Load strategy configuration (mutable parameters)."""
        config_path = Path(__file__).parent.parent / "strategy_config.json"
        if not config_path.exists():
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ReflectionEngine] Failed to load strategy config: {e}")
            return {}

    @staticmethod
    def save_config(config):
        """Save strategy configuration."""
        config_path = Path(__file__).parent.parent / "strategy_config.json"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ReflectionEngine] Failed to save strategy config: {e}")

    @staticmethod
    def save_state(state):
        try:
            with open(ReflectionEngine.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[ReflectionEngine] Failed to save state: {e}")

    @staticmethod
    def mutate_strategy(strategy_id, current_config, mutation_config):
        """
        Mutation Logic: Randomly adjust a parameter if performance is poor.
        """
        import random
        strategy_params = current_config.get("strategies", {}).get(strategy_id)
        if not strategy_params:
            return current_config

        # 1. Decide what to mutate (RSI, F-Score, MA)
        choice = random.choice(["rsi_threshold", "f_score_min", "min_ma_window"])
        
        old_val = strategy_params.get(choice)
        new_val = old_val

        if choice == "rsi_threshold":
            step = mutation_config.get("rsi_step", 2)
            # 50% chance to increase or decrease, constrained by min/max
            change = random.choice([-step, step])
            new_val = max(mutation_config.get("min_rsi", 20), min(mutation_config.get("max_rsi", 80), old_val + change))
        
        elif choice == "f_score_min":
            step = mutation_config.get("f_score_step", 1)
            change = random.choice([-step, step])
            new_val = max(0, min(9, old_val + change))
            
        # Update config
        strategy_params[choice] = new_val
        current_config["strategies"][strategy_id] = strategy_params
        
        print(f"[Evolution] Mutated {strategy_id} {choice}: {old_val} -> {new_val}")
        return current_config


    @staticmethod
    def run_daily_reflection(predicted_stocks, actual_performance):
        """
        執行每日反思與權重微調核心邏輯
        :param predicted_stocks: 昨日推薦清單與預期分數
        :param actual_performance: 今日實測漲跌幅 (dict, 需含 avg_return)
        :return: list of reflection messages
        """
        state = ReflectionEngine.load_state()
        strategies = state.get("strategies", {})

        if not strategies:
            print("[ReflectionEngine] No strategies found, skipping reflection.")
            return []

        learning_rate = state.get("mutation_config", {}).get("learning_rate", 0.01)
        reflections = []

        # Load Mutable Config
        config = ReflectionEngine.load_config()
        mutation_config = config.get("mutation_config", {})
        
        for s_id, strategy in strategies.items():
            current_weights = strategy.get("weights", {})
            new_weights = current_weights.copy()

            # [自進化邏輯] 若整體表現低於預期，進行探索性微調 (Mutation)
            avg_return = actual_performance.get("avg_return", 0)
            
            # TRIGGER MUTATION if return is very bad (e.g. < -5%) or just negative
            if avg_return < -0.01:
                EvolutionManager.log_anomaly(
                    "EVOLUTION_TRIGGER",
                    f"策略 {s_id} 表現不佳 (avg_return={avg_return:.4f})，觸發突變"
                )
                
                # 1. Adjust Weights (Level 1 Evolution)
                new_weights["eps_growth"] = round(new_weights.get("eps_growth", 0) + learning_rate, 3)
                new_weights["fScore"] = round(new_weights.get("fScore", 0) - learning_rate, 3)
                
                # 2. Mutate Parameters (Level 2 Evolution)
                # Modify strategy_config.json directly
                config = ReflectionEngine.mutate_strategy(s_id, config, mutation_config)
                ReflectionEngine.save_config(config)
                
                history_entry = {
                    "date": datetime.now().isoformat(),
                    "avg_return": avg_return,
                    "weights_after": new_weights,
                    "mutations": "Triggered parameter mutation",
                    "reflection": f"Mutated {s_id} params and weights based on market response."
                }
            else:
                 history_entry = {
                    "date": datetime.now().isoformat(),
                    "avg_return": avg_return,
                    "weights_after": new_weights,
                    "reflection": f"Strategy {s_id} performing within expectations."
                }

            # ✅ 修復：在迴圈內更新各自策略的 weights
            strategy["weights"] = new_weights
            
            # ✅ 修復：Rolling window，避免無限增長
            if "performance_history" not in strategy:
                strategy["performance_history"] = []
            strategy["performance_history"].append(history_entry)
            if len(strategy["performance_history"]) > ReflectionEngine.MAX_HISTORY:
                strategy["performance_history"] = strategy["performance_history"][-ReflectionEngine.MAX_HISTORY:]

            reflections.append(history_entry["reflection"])

        state["last_reflection"] = datetime.now().isoformat()
        ReflectionEngine.save_state(state)

        return reflections


if __name__ == "__main__":
    # 測試模擬執行
    results = ReflectionEngine.run_daily_reflection(
        predicted_stocks=[],
        actual_performance={"avg_return": -0.02}
    )
    print(results)

# TwStockVision / Self-Evolving Alpha Lab 🇹🇼📈

![Dashboard Preview](public/dashboard-preview.png)

> **自進化 Alpha Lab**：這不只是一個儀表板，而是一個會每天學習、反思並自我優化的 AI 投資助手。

## ✨ 核心進化功能 (Alpha Lab Evolution)

### 1. 🧠 AI 自進化核心 (Dynamic Strategy Optimization)
系統內建「反思引擎 (Reflection Engine)」，不再固定選股邏輯：
- **每日反思**：每天 14:30 自動分析當日選股績效，歸因成功與失敗因素。
- **權重演進**：動態調整成長、價值、現金流等因子權重，並可視化於「進化雷達圖」。
- **版本控制**：每一代策略都有版本號，確保進化軌跡可追溯。

### 2. 🛡️ 自癒資料管線 (Self-Healing Data Pipeline)
具備強大的環境適應能力：
- **主動偵測**：即時監控 TradingView/TVScreener 資料完整性。
- **自動降級**：當主資料源發生缺失 (DATA_MISSING) 時，秒級切換至 yfinance 備援。
- **異常日誌**：所有自癒過程皆記錄於演化日誌，作為 AI 下次進化的參考。

### 3. 📊 進化視覺化儀表板
- **策略雷達圖**：直觀展示 AI 當前的大腦配比。
- **進度日誌**：紀錄 AI 每一次「頓悟」的過程與報酬率歸因。

## 🛠️ 技術棧 (Modern Fintech Stack)

- **前端**: Next.js 14, React, Framer Motion (Premium UI), Recharts (Strategy Visualization)
- **後端**: Python (Agentic Framework), Reflection Engine
- **記憶層**: Evolution State Manager (Persistent AI Learning)
- **資料來源**: TradingView GSG, yfinance, TWSE ISIN Data

## 🚀 快速啟動

```bash
# 1. 安裝環境
npm install
pip install -r requirements.txt

# 2. 啟動選股引擎與 API
python run_local_api.py

# 3. 開啟前端介面
npm run dev
```

## 📈 未來展望
- **異構資料融合**：加入新聞情緒分析作為新的演化維度。
- **虛擬沙盒**：在正式應用新權重前，先在 Shadow Mode 進行 24 小時模擬測試。

---
Developed with AI Evolution Protocol | **Alpha Lab v1.2**

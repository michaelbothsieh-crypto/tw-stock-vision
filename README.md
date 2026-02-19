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

## 🌐 線上版

👉 **[tw-stock-vision.vercel.app](https://tw-stock-vision.vercel.app)**

> 已部署於 Vercel，開啟即可使用，無需安裝。

## �️ 如何使用

### 主儀表板
開啟網站後，你會看到**台股熱門排行**，系統已自動從 TradingView 抓取最新數據：

| 區域 | 說明 |
|------|------|
| 🔍 **搜尋列** | 輸入股票代號（如 `2330`）或名稱（如 `台積電`），即時查詢任意台股 |
| 📊 **個股卡片** | 點擊任一股票，下方展開詳細資訊：股價走勢圖、RSI、成交量、漲跌幅 |
| �📈 **K 線圖** | 支援切換時間區間（1 個月 / 3 個月 / 1 年），滑鼠懸停可查看當日數據 |
| 🏆 **熱門排行** | 依據 AI 評分與市場動量排序的台股推薦清單 |

### AI 自進化面板
往下捲動至「**AI 自進化核心**」區塊：

- **策略雷達圖**：顯示 AI 目前各因子權重（EPS 成長、F-Score、毛利率等），形狀越飽滿代表權重越均衡
- **策略版本號**：每次 AI 自動進化後版本號會遞增（如 `1.0.0 → 1.0.1`）
- **預測追蹤看板**：顯示 AI 預測總數、已結算數、準確率與平均報酬率
- **進化日誌**：時間軸卡片紀錄每次 AI 的反思結論、報酬率與參數突變事件

### 使用流程

```
1. 瀏覽首頁  →  查看熱門台股排行
2. 搜尋股票  →  輸入代號查看詳細走勢
3. 觀察 AI   →  下滑查看 AI 策略雷達圖與進化日誌
4. 持續使用  →  AI 會在背景自動學習並優化選股策略
```

> 💡 **提示**：你不需要手動觸發任何 AI 功能。系統會在你每次瀏覽時，自動在背景進行預測結算與策略反思。

## 📈 未來展望
- **異構資料融合**：加入新聞情緒分析作為新的演化維度。
- **虛擬沙盒**：在正式應用新權重前，先在 Shadow Mode 進行 24 小時模擬測試。
- **Vercel Cron**：定時排程批次結算，不再依賴使用者訪問觸發。

---
Developed with AI Evolution Protocol | **Alpha Lab v1.2**

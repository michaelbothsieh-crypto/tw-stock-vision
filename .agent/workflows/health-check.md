---
description: 診斷系統健康狀態 (Backend & Frontend Check)
---

此 Workflow 用於快速診斷 TwStockVision 的後端 API 與前端連線狀態。

1. 檢查後端 API 健康狀態
// turbo
curl -I http://localhost:3000/api/stock?trending=true

2. 測試單一股票數據抓取 (台積電 2330)
// turbo
curl "http://localhost:3000/api/stock?symbol=2330"

3. 檢查 Python 後端 Process
// turbo
tasklist /FI "IMAGENAME eq python.exe"

4. 檢查 Node.js 前端 Process
// turbo
tasklist /FI "IMAGENAME eq node.exe"

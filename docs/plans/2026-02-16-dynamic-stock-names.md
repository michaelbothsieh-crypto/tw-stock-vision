# 動態股票名稱服務實作計畫 (Dynamic Stock Name Service Implementation Plan)

> **給 Agent:** 必要子技能: 使用 `superpowers:executing-plans` 來逐項執行此計畫。

**目標:** 將硬編碼的 `TW_STOCK_NAMES` 字典替換為自動從 `twstock` 函式庫獲取所有台股（上市與上櫃）中文名稱的動態服務。

**架構:** 
我們將整合 `twstock` Python 函式庫，該庫維護了完整的股票代碼列表。我們將建立一個新的服務模組 `api/services/stock_names.py` 來封裝抓取邏輯，並在應用程式啟動時填充名稱對照表，取代原本的手動維護方式。

**技術堆疊:** `python`, `twstock` library

---

### 任務 1: 安裝並驗證 `twstock` (Install and Verify)

**檔案:**
- 修改: `requirements.txt` (如果存在，或是確保環境已安裝)
- 新增: `scripts/verify_twstock.py`

**步驟 1: 撰寫驗證腳本 (預期失敗)**

建立一個腳本來確認我們要使用的 `twstock` 屬性是否存在。

```python
# scripts/verify_twstock.py
import twstock

def test_fetch_name():
    # 驗證 2330 是否為台積電
    print(f"2330 Name: {twstock.codes['2330'].name}")
    assert twstock.codes['2330'].name == "台積電"
    
    # 驗證上櫃公司 (例如 6223 旺矽)
    print(f"6223 Name: {twstock.codes['6223'].name}")
    assert '6223' in twstock.codes
    
if __name__ == "__main__":
    test_fetch_name()
```

**步驟 2: 執行驗證**

執行: `python scripts/verify_twstock.py`
預期: PASS (因為我們剛剛已經 pip install 過了，確認庫功能正常)

**步驟 3: 提交 (Commit)**

```bash
git add scripts/verify_twstock.py
git commit -m "chore: verify twstock library availability"
```

### 任務 2: 建立股票名稱服務 (Create Stock Name Service)

**檔案:**
- 新增: `api/services/__init__.py`
- 新增: `api/services/stock_names.py`
- 測試: `tests/test_stock_names_service.py`

**步驟 1: 撰寫服務測試 (預期失敗)**

```python
# tests/test_stock_names_service.py
import sys
import os
sys.path.append(os.getcwd())
try:
    from api.services.stock_names import get_all_stock_names
except ImportError:
    pass # 預期失敗

def test_get_all_names():
    # 只有當模組存在時才執行測試
    try:
        from api.services.stock_names import get_all_stock_names
        names = get_all_stock_names()
        assert isinstance(names, dict)
        assert names['2330'] == '台積電'
        assert len(names) > 1000  # 應該要有數千檔股票
        print(f"Successfully fetched {len(names)} stocks")
    except ImportError:
        assert False, "Module api.services.stock_names not found"
    
if __name__ == "__main__":
    test_get_all_names()
```

**步驟 2: 執行測試**

執行: `python tests/test_stock_names_service.py`
預期: FAIL (ImportError)

**步驟 3: 實作服務邏輯**

```python
# api/services/stock_names.py
import twstock

def get_all_stock_names():
    """
    從 twstock 獲取所有上市櫃股票名稱。
    回傳字典格式: {symbol: name}
    """
    mapping = {}
    # twstock.codes 包含所有上市櫃資訊
    for code, info in twstock.codes.items():
        if info.type == '股票': # 只過濾出股票，排除 ETF 等其他商品若不需要
            mapping[code] = info.name
            
    return mapping
```

**步驟 4: 再次執行測試**

執行: `python tests/test_stock_names_service.py`
預期: PASS

**步驟 5: 提交**

```bash
git add api/services/stock_names.py tests/test_stock_names_service.py api/services/__init__.py
git commit -m "feat: implement dynamic stock name service using twstock"
```

### 任務 3: 整合至 API 常數 (Integrate)

**檔案:**
- 修改: `api/constants.py`
- 修改: `api/index.py`

**步驟 1: 修改 constants.py**

將 `TW_STOCK_NAMES` 初始化為空字典，等待啟動時注入。或保留部分熱門股作為 fallback。

**步驟 2: 修改 index.py 進行啟動時載入**

```python
# api/index.py (加入以下邏輯)
from api.services.stock_names import get_all_stock_names
from api.constants import TW_STOCK_NAMES

# 伺服器啟動時執行
try:
    print("正在載入動態股票名稱...")
    dynamic_names = get_all_stock_names()
    TW_STOCK_NAMES.update(dynamic_names)
    print(f"成功載入 {len(TW_STOCK_NAMES)} 檔股票名稱。")
except Exception as e:
    print(f"載入股票名稱失敗: {e}")
```

**步驟 3: 驗證整合**

執行: `curl "http://localhost:3000/api/stock?symbol=6223"`
預期: 回傳名稱為 "旺矽" (原本字典裡沒有的)

**步驟 4: 提交**

```bash
git add api/constants.py api/index.py
git commit -m "refactor: integrate dynamic stock names into api startup"
```

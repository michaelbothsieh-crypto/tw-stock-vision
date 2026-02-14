import sys
import os
import json

# 加入當前目錄到 path 以載入 api.index
sys.path.append(os.getcwd())

from api.index import handler
from unittest.mock import MagicMock

class MockRequest:
    def __init__(self, path):
        self.path = path

def test_2408_fusion():
    print("=== Testing Fusion Logic for 2408.TW ===")
    from api.index import handler
    h = handler(MockRequest("/api/stock?symbol=2408"), ("127.0.0.1", 80), None)
    h.wfile = MagicMock()
    
    # 調用處理邏輯
    handler._handle_stock_lookup("2408")
    
    # 獲取寫入的內容
    args, _ = handler.wfile.write.call_args
    output = json.loads(args[0].decode('utf-8'))
    
    print(f"Symbol: {output.get('symbol')}")
    print(f"Target Price: {output.get('targetPrice')}")
    print(f"Price: {output.get('price')}")
    
    if output.get('targetPrice') > 100:
        print("SUCCESS: Target price is in TWD range!")
    else:
        print(f"FAILURE: Target price {output.get('targetPrice')} is still too low (ADR/US overlap?)")

if __name__ == "__main__":
    test_2408_fusion()

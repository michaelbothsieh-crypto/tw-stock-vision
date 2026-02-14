from api.index import handler
import json

class MockRequest:
    def __init__(self, path):
        self.path = path
    def makefile(self, *args, **kwargs):
        import io
        return io.BytesIO(b"")

def test_trending():
    print("Testing Trending API directly...")
    h = handler(MockRequest("/api/market/trending?market=TW"), ("127.0.0.1", 80), None)
    from unittest.mock import MagicMock
    h.wfile = MagicMock()
    h._handle_market_trending()
    
    args, _ = h.wfile.write.call_args
    data = json.loads(args[0].decode('utf-8'))
    print(f"Results Count: {len(data)}")
    if data:
        print(f"Sample: {data[0]}")
    else:
        print("EMPTY RESULTS!")

if __name__ == "__main__":
    test_trending()

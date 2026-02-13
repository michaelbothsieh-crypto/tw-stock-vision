import sys
import os
import json

# Add api to path so we can import index
sys.path.append(os.path.join(os.getcwd(), 'api'))

try:
    import index
    
    # Mock class inheriting from index.handler to test real logic
    class TestHandler(index.handler):
        def __init__(self):
            self.path = '/api/stock?symbol=2330'
            self.wfile = type('WFile', (object,), {'write': self.write})()
            self.rfile = None
            
        def write(self, data):
            print("--- RESPONSE START ---")
            try:
                print(data.decode('utf-8'))
            except:
                print(data)
            print("--- RESPONSE END ---")
            
        def _set_headers(self):
            print("Headers set")
            
    print("Initializing handler...")
    # Instantiate without calling BaseHTTPRequestHandler.__init__
    h = TestHandler()
    print("Running do_GET...")
    h.do_GET()
    
except Exception as e:
    import traceback
    traceback.print_exc()

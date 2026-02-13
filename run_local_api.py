from http.server import HTTPServer, ThreadingHTTPServer
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from api.index import handler, init_db
    # Initialize DB tables
    print("Initializing Database...")
    init_db()
except Exception as e:
    print(f"Import/Init Error: {e}")
    sys.exit(1)

def run(server_class=ThreadingHTTPServer, handler_class=handler, port=8000):
    server_address = ('0.0.0.0', port)
    try:
        httpd = server_class(server_address, handler_class)
        print(f"Starting local API server on http://0.0.0.0:{port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"Server Error: {e}")

if __name__ == "__main__":
    run()

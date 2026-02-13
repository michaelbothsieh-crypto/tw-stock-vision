from http.server import HTTPServer
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from api.index import handler
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def run(server_class=HTTPServer, handler_class=handler, port=8000):
    server_address = ('127.0.0.1', port)
    try:
        httpd = server_class(server_address, handler_class)
        print(f"Starting local API server on http://127.0.0.1:{port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"Server Error: {e}")

if __name__ == "__main__":
    run()

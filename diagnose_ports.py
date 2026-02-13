import socket
import sys

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

ports = [3000, 8000]
for p in ports:
    status = "OPEN" if check_port(p) else "CLOSED"
    print(f"Port {p}: {status}")

if not check_port(8000):
    print("CRITICAL: Python Backend (Port 8000) is NOT running!")
if not check_port(3000):
    print("WARNING: Next.js Frontend (Port 3000) seems down.")

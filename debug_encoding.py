
import sys
from urllib.parse import unquote

def test_encoding(val):
    print(f"Input: {val}")
    try:
        re_encoded = val.encode('latin-1').decode('utf-8')
        print(f"Latin-1 to UTF-8: {re_encoded}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_encoding(sys.argv[1])

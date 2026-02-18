import time
import sys
import os

def benchmark_import():
    sys.path.append(os.getcwd())
    start = time.time()
    print("Starting import benchmark for api.index...")
    try:
        import api.index
        end = time.time()
        duration = end - start
        print(f"Import api.index took: {duration:.4f} seconds")
        if duration < 1.0:
            print("SUCCESS: Startup latency is within acceptable limits (< 1s).")
        else:
            print("WARNING: Startup latency exceeds 1s. Further optimization may be needed.")
    except Exception as e:
        print(f"Import failed: {e}")

if __name__ == "__main__":
    benchmark_import()

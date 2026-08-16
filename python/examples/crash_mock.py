import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def buggy_function():
    print("[*] Running preliminary data validation...")
    time.sleep(1.5)
    print("❌ Fatal: Memory allocation failed or division by zero!")
    time.sleep(0.5)
    raise ValueError("CUDA out of memory: tried to allocate 8.00 GiB (GPU 0; 4.00 GiB total capacity)")

if __name__ == "__main__":
    buggy_function()

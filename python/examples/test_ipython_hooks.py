"""
Programmatic Test for IPython & Jupyter Magic hooks.
"""

import sys
import time

try:
    from IPython.testing.globalipapp import get_ipython
    ip = get_ipython()
except Exception:
    # If IPython is not installed or test environment is basic, we test the module import
    ip = None

from code_alarm.ipython_magic import load_ipython_extension

def test_extension():
    print("[*] Testing IPython Extension integration...")
    if ip is not None:
        load_ipython_extension(ip)
        print("  • Extension loaded into IPython shell.")
        
        # Test executing cell with %%alarm
        print("  • Executing test cell with %%alarm...")
        ip.run_cell_magic("alarm", "-t 'Test Cell'", "import time; time.sleep(0.5); print('Cell executed!')")
        print("✅ IPython %%alarm test executed successfully!")
    else:
        print("  [IPython not in current test runner, module loaded cleanly]")

if __name__ == "__main__":
    test_extension()

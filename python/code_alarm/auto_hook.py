"""
Global Python Auto-Notifier Hook (usercustomize.py)
----------------------------------------------------
When active, ANY Python script executed anywhere on this laptop (via VS Code Green Play button,
terminal 'python file.py', debugger, etc.) will automatically chime and show a desktop toast popup
when it finishes execution!
"""

import sys
import os
import time
import atexit

# Only trigger if the script took longer than this threshold (seconds)
# (e.g. 2.0 seconds so fast commands like 'python --version' stay quiet)
MIN_DURATION_SECONDS = 1.5

_start_time = time.time()
_exception_occurred = False
_exception_info = ""

def _global_exception_handler(exc_type, exc_value, exc_traceback):
    global _exception_occurred, _exception_info
    _exception_occurred = True
    _exception_info = f"{exc_type.__name__}: {exc_value}"
    # Call original exception handler so traceback prints normally
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = _global_exception_handler

def _on_exit_hook():
    global _start_time, _exception_occurred, _exception_info
    
    # Determine script name
    if sys.argv and sys.argv[0]:
        if sys.argv[0] == "-c":
            script_name = "Python Code"
        else:
            script_name = os.path.basename(sys.argv[0])
    else:
        script_name = "Python Script"

    # Skip internal python tools and pip commands
    if script_name.lower() in ("pip", "pip.exe", "setuptools"):
        return

    elapsed = time.time() - _start_time

    if elapsed >= MIN_DURATION_SECONDS:
        try:
            # Import code_alarm laptop alert engine
            from code_alarm.laptop_alerts import trigger_laptop_alert
            
            hrs = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            secs = elapsed % 60
            dur_str = f"{hrs}h {mins}m {secs:.1f}s" if hrs > 0 else (f"{mins}m {secs:.1f}s" if mins > 0 else f"{secs:.1f}s")

            if _exception_occurred:
                trigger_laptop_alert(
                    title=f"❌ {script_name} Failed",
                    message=f"Crashed after {dur_str}: {_exception_info[:60]}",
                    pattern="ERROR",
                    voice=False
                )
            else:
                pattern = "TRAIN_DONE" if elapsed > 30 else "SUCCESS"
                trigger_laptop_alert(
                    title=f"✅ {script_name} Finished",
                    message=f"Execution completed in {dur_str}",
                    pattern=pattern,
                    voice=False
                )
            # Short pause so audio thread can initiate before process fully dies
            time.sleep(0.35)
        except Exception:
            pass

atexit.register(_on_exit_hook)

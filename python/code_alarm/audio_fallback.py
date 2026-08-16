"""
Audio fallback using built-in system sound (winsound on Windows, ASCII bell / os tones elsewhere)
Ensures you still get audible feedback even when the microcontroller is unplugged.
"""

import sys
import time
import threading

def _beep_windows(freq: int, duration_ms: int):
    try:
        import winsound
        winsound.Beep(freq, duration_ms)
    except Exception:
        # Fallback terminal bell
        print("\a", end="", flush=True)

def _play_pattern(pattern_name: str):
    pattern_name = pattern_name.upper()
    
    if pattern_name in ("SUCCESS", "DONE", "1"):
        # 1 clean uplifting tone
        _beep_windows(2600, 250)
        
    elif pattern_name in ("ERROR", "FAIL", "CRASH", "2"):
        # 2 warning tones
        _beep_windows(1800, 120)
        time.sleep(0.08)
        _beep_windows(1400, 250)
        
    elif pattern_name in ("TRAIN_DONE", "TRAIN_SUCCESS", "3"):
        # 3 victory tones
        _beep_windows(2000, 100)
        time.sleep(0.06)
        _beep_windows(2400, 100)
        time.sleep(0.06)
        _beep_windows(2900, 300)
        
    elif pattern_name in ("ALERT", "CRITICAL", "4"):
        # Rapid alerts
        for _ in range(6):
            _beep_windows(3000, 120)
            time.sleep(0.08)
            
    elif pattern_name in ("TEST",):
        _beep_windows(2400, 200)
        time.sleep(0.2)
        _beep_windows(1800, 200)
    else:
        _beep_windows(2000, 200)

def play_software_fallback(pattern_name: str, async_mode: bool = True):
    """Play software sound fallback on laptop speakers."""
    if async_mode:
        t = threading.Thread(target=_play_pattern, args=(pattern_name,), daemon=True)
        t.start()
    else:
        _play_pattern(pattern_name)

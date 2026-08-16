"""
Application Lifecycle & Single-Instance Manager for Code Alarm V2.
Manages:
- Single instance protection (named mutex & socket lock)
- Server readiness polling and port conflict resolution
- Optional per-user "Start with Windows" configuration (HKCU Run key)
"""

import os
import sys
import time
import socket
import urllib.request
import urllib.error
import threading
from pathlib import Path
from typing import Optional, Tuple

LOCK_PORT = 8089
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8088

_lock_socket: Optional[socket.socket] = None
_mutex_handle = None

# ── SINGLE-INSTANCE LOCK ──────────────────────────────────────────────────────
def acquire_single_instance_lock() -> bool:
    """
    Attempt to acquire the single-instance lock.
    Uses Windows Named Mutex for instantaneous OS-level single-instance enforcement.
    Returns True if this is the first running instance.
    Returns False if an existing instance is already running.
    """
    global _mutex_handle, _lock_socket
    if sys.platform == "win32":
        try:
            import ctypes
            CreateMutexW = ctypes.windll.kernel32.CreateMutexW
            GetLastError = ctypes.windll.kernel32.GetLastError
            ERROR_ALREADY_EXISTS = 183

            mutex_name = "Local\\CodeAlarm_V2_SingleInstance_Mutex"
            handle = CreateMutexW(None, True, mutex_name)
            if GetLastError() == ERROR_ALREADY_EXISTS:
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                return False
            _mutex_handle = handle
            return True
        except Exception:
            pass

    # Socket fallback (exclusive binding)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((SERVER_HOST, LOCK_PORT))
        s.listen(1)
        _lock_socket = s
        return True
    except OSError:
        return False

def release_single_instance_lock():
    """Release single instance lock."""
    global _mutex_handle, _lock_socket
    if _mutex_handle and sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        except Exception:
            pass
        _mutex_handle = None

    if _lock_socket:
        try:
            _lock_socket.close()
        except Exception:
            pass
        _lock_socket = None

def notify_existing_instance() -> bool:
    """
    Notify the existing Code Alarm instance to wake up and focus its dashboard window.
    """
    try:
        req = urllib.request.Request(
            f"http://{SERVER_HOST}:{SERVER_PORT}/api/wake",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status == 200
    except Exception:
        return False

# ── SERVER READINESS & LIFECYCLE ──────────────────────────────────────────────
def is_server_ready(host: str = SERVER_HOST, port: int = SERVER_PORT) -> bool:
    """Check if the Code Alarm REST API server is responsive."""
    url = f"http://{host}:{port}/api/ping"
    try:
        with urllib.request.urlopen(url, timeout=0.6) as resp:
            if resp.status == 200:
                data = resp.read().decode("utf-8")
                return "CodeAlarm" in data
    except Exception:
        pass
    return False

def ensure_server_running(host: str = SERVER_HOST, port: int = SERVER_PORT, timeout_seconds: float = 5.0) -> bool:
    """
    Ensure the local Code Alarm dashboard server is running and ready.
    Reuses existing server if already healthy. Spawns background thread if needed.
    Waits for readiness before returning.
    """
    if is_server_ready(host, port):
        return True

    # Import server module
    try:
        from web_dashboard.server import start_server
    except ImportError:
        # Try from sys.path
        dashboard_dir = Path(__file__).resolve().parent.parent.parent / "web_dashboard"
        if str(dashboard_dir) not in sys.path:
            sys.path.insert(0, str(dashboard_dir))
        from server import start_server

    # Launch server in a background daemon thread
    server_thread = threading.Thread(
        target=start_server,
        kwargs={"open_browser": False, "host": host, "port": port},
        daemon=True,
        name="CodeAlarm-ServerThread"
    )
    server_thread.start()

    # Poll for readiness
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_server_ready(host, port):
            return True
        time.sleep(0.08)

    return is_server_ready(host, port)

# ── START WITH WINDOWS (HKCU RUN KEY) ─────────────────────────────────────────
AUTOSTART_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_APP_NAME = "CodeAlarm"

def is_autostart_enabled() -> bool:
    """Check if Code Alarm is set to launch on Windows startup."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_APP_NAME)
            return bool(value)
    except Exception:
        return False

def set_autostart(enabled: bool) -> bool:
    """
    Enable or disable Code Alarm startup with Windows (per-user registry key).
    Zero administrator rights required.
    """
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                if getattr(sys, "frozen", False):
                    # Running as compiled executable
                    cmd = f'"{sys.executable}" --background'
                else:
                    # Running from Python source
                    desktop_script = Path(__file__).resolve().parent.parent.parent / "desktop_app.py"
                    cmd = f'"{sys.executable}" "{desktop_script}" --background'
                winreg.SetValueEx(key, AUTOSTART_APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"Failed to update autostart: {e}")
        return False

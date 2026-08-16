"""
Code Alarm V2 — Desktop Application Engine (PyWebView + System Tray)
Wraps the existing V2 Web Dashboard and Monitoring Engine into a permanent
Windows desktop application.
Safe ASCII console outputs ensure total compatibility with Windows CP1252 windowed mode.
"""

import sys
import os
import time
import threading
from pathlib import Path
from typing import Optional

try:
    import webview
except ImportError:
    webview = None

from .app_lifecycle import (
    acquire_single_instance_lock,
    release_single_instance_lock,
    notify_existing_instance,
    ensure_server_running,
    SERVER_HOST,
    SERVER_PORT
)
from .tray import SystemTrayManager
from .resources import get_icon_path

class DesktopApp:
    def __init__(self, start_in_background: bool = False):
        self.start_in_background = start_in_background
        self.window: Optional[webview.Window] = None
        self.tray: Optional[SystemTrayManager] = None
        self._is_shutting_down = False

    def show_dashboard(self):
        """Restore and focus the dashboard window."""
        if self.window:
            try:
                self.window.show()
                self.window.restore()
            except Exception:
                pass
        else:
            # Asynchronously open browser if running in headless background mode
            import webbrowser
            threading.Thread(
                target=webbrowser.open,
                args=(f"http://{SERVER_HOST}:{SERVER_PORT}",),
                daemon=True
            ).start()

    def on_window_closing(self):
        """
        Intercept window closing: Hide the window to system tray instead of terminating,
        preserving active background job monitoring and alerts.
        """
        if self._is_shutting_down:
            return True  # Allow close

        # Hide window to tray
        if self.window:
            self.window.hide()
        return False  # Prevent window destruction

    def shutdown(self):
        """Perform a clean shutdown of the application."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        print("\n[INFO] Shutting down Code Alarm...")

        # 1. Stop Tray
        if self.tray:
            self.tray.stop()

        # 2. Destroy Webview Window
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass

        # 3. Stop Server
        try:
            from web_dashboard.server import stop_server
            stop_server()
        except Exception:
            pass

        # 4. Release Lock
        release_single_instance_lock()
        print("[OK] Code Alarm clean shutdown complete.")
        sys.exit(0)

    def run(self):
        # 1. Single Instance Check
        if not acquire_single_instance_lock():
            print("[INFO] Code Alarm is already running. Focusing existing window...")
            notify_existing_instance()
            sys.exit(0)

        # 2. Ensure local server is ready
        print("[INFO] Initializing Code Alarm background engine...")
        if not ensure_server_running(SERVER_HOST, SERVER_PORT, timeout_seconds=6.0):
            print("[ERROR] Failed to start dashboard server.")
            release_single_instance_lock()
            sys.exit(1)

        # Register wake callback on server
        try:
            from web_dashboard.server import set_wake_callback
            set_wake_callback(self.show_dashboard)
        except Exception:
            pass

        # 3. Initialize and Start System Tray
        self.tray = SystemTrayManager(
            on_open_dashboard=self.show_dashboard,
            on_exit=self.shutdown
        )
        self.tray.start()
        print("[OK] System Tray active. Background monitoring enabled.")

        # 4. If starting in background, keep process alive without webview
        if self.start_in_background or not webview:
            print("[INFO] Code Alarm running in background mode.")
            try:
                while not self._is_shutting_down:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                self.shutdown()
            return

        # 5. Create PyWebView Window
        dashboard_url = f"http://{SERVER_HOST}:{SERVER_PORT}"
        self.window = webview.create_window(
            title="Code Alarm V2 — Intelligent Developer Execution & Alert System",
            url=dashboard_url,
            width=1140,
            height=760,
            min_size=(860, 600),
            background_color="#080b11"
        )
        self.window.events.closing += self.on_window_closing

        # Start Webview GUI event loop
        try:
            webview.start(gui="edgechromium")
        except Exception:
            try:
                webview.start()
            except Exception as e:
                print(f"[WARN] Webview failed to start: {e}. Falling back to background mode.")
                while not self._is_shutting_down:
                    time.sleep(1.0)
        finally:
            self.shutdown()

def launch_desktop(background: bool = False):
    app = DesktopApp(start_in_background=background)
    app.run()

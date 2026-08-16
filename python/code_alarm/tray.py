"""
Windows System Tray Integration for Code Alarm V2.
Provides a persistent background tray icon with live status,
quick dashboard access, Quiet Mode toggle, Autostart toggle, and clean exit.
"""

import sys
import threading
from typing import Callable, Optional
from pathlib import Path
from PIL import Image

try:
    import pystray
    from pystray import MenuItem as item, Menu
except ImportError:
    pystray = None

from .config import config
from .resources import get_icon_path
from .app_lifecycle import is_autostart_enabled, set_autostart

class SystemTrayManager:
    """
    Manages the Windows notification area (System Tray) icon for Code Alarm.
    """
    def __init__(
        self,
        on_open_dashboard: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None
    ):
        self.on_open_dashboard = on_open_dashboard
        self.on_exit = on_exit
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _load_image(self) -> Image.Image:
        png_path = get_icon_path("png")
        if png_path.exists():
            return Image.open(str(png_path))
        ico_path = get_icon_path("ico")
        if ico_path.exists():
            return Image.open(str(ico_path))
        # Fallback: create a solid 32x32 blue image
        return Image.new("RGBA", (32, 32), (59, 130, 246, 255))

    def _toggle_quiet_mode(self, icon, item):
        current = config.is_quiet_mode()
        config.set("quiet_mode", not current)
        icon.update_menu()

    def _toggle_autostart(self, icon, item):
        current = is_autostart_enabled()
        set_autostart(not current)
        icon.update_menu()

    def _create_menu(self) -> pystray.Menu:
        return Menu(
            item("🔔 Code Alarm V2", lambda: None, enabled=False),
            item("🟢 Monitoring Active", lambda: None, enabled=False),
            Menu.SEPARATOR,
            item("📊 Open Dashboard", lambda: self.on_open_dashboard() if self.on_open_dashboard else None, default=True),
            item(
                "🔕 Quiet Mode",
                self._toggle_quiet_mode,
                checked=lambda item: config.is_quiet_mode()
            ),
            item(
                "🚀 Start with Windows",
                self._toggle_autostart,
                checked=lambda item: is_autostart_enabled()
            ),
            Menu.SEPARATOR,
            item("❌ Exit Code Alarm", lambda: self._handle_exit())
        )

    def _handle_exit(self):
        if self.icon:
            self.icon.stop()
        if self.on_exit:
            self.on_exit()

    def start(self):
        """Start the system tray icon in a dedicated background daemon thread."""
        if not pystray:
            print("Warning: pystray not installed, system tray disabled.")
            return

        def _run():
            img = self._load_image()
            menu = self._create_menu()
            self.icon = pystray.Icon(
                "CodeAlarm",
                img,
                "Code Alarm V2 — Monitoring Active",
                menu=menu
            )
            self.icon.run()

        self._thread = threading.Thread(target=_run, daemon=True, name="CodeAlarm-TrayThread")
        self._thread.start()

    def stop(self):
        """Stop and remove the system tray icon."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None

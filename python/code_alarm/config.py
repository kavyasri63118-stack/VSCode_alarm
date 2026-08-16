"""
Persistent Configuration Engine for Alert Control Center
Stores the 7 primary settings in ~/.code_alarm/config.json with zero hard-coded paths.
"""

import json
import threading
from pathlib import Path
from typing import Dict, Any
from .storage import get_code_alarm_dir

CONFIG_FILE_NAME = "config.json"

DEFAULT_SETTINGS: Dict[str, bool] = {
    "master_alert_system": True,
    "success_sound": True,
    "failure_sound": True,
    "desktop_notification": True,
    "failure_intelligence": True,
    "job_summary": True,
    "quiet_mode": False
}

class ConfigManager:
    """
    Thread-safe persistent configuration manager.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._config_file = get_code_alarm_dir() / CONFIG_FILE_NAME
                cls._instance._settings = {}
                cls._instance.load()
            return cls._instance

    def load(self) -> Dict[str, bool]:
        """Load settings from disk or initialize defaults."""
        with self._lock:
            if self._config_file.exists():
                try:
                    with open(self._config_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Merge with defaults in case of missing keys
                    self._settings = {**DEFAULT_SETTINGS, **{k: bool(v) for k, v in data.items() if k in DEFAULT_SETTINGS}}
                except Exception:
                    self._settings = DEFAULT_SETTINGS.copy()
            else:
                self._settings = DEFAULT_SETTINGS.copy()
                self._save_unlocked()
            return self._settings.copy()

    def _save_unlocked(self):
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"[CODE-ALARM] Warning: Failed to persist config: {e}")

    def save(self):
        """Save settings to disk."""
        with self._lock:
            self._save_unlocked()

    def get_all(self) -> Dict[str, bool]:
        """Return a copy of all 7 settings."""
        with self._lock:
            return self._settings.copy()

    def get(self, key: str, default: bool = True) -> bool:
        """Get a single setting value."""
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value: bool) -> Dict[str, bool]:
        """Set a single setting and persist to disk."""
        with self._lock:
            if key in DEFAULT_SETTINGS:
                self._settings[key] = bool(value)
                self._save_unlocked()
            return self._settings.copy()

    def set_many(self, updates: Dict[str, Any]) -> Dict[str, bool]:
        """Update multiple settings simultaneously."""
        with self._lock:
            for k, v in updates.items():
                if k in DEFAULT_SETTINGS:
                    self._settings[k] = bool(v)
            self._save_unlocked()
            return self._settings.copy()

    def get_effective_all(self) -> Dict[str, bool]:
        """
        Calculate effective runtime status of all 7 settings.
        Quiet Mode and Master Alert OFF act as runtime suppression layers
        without modifying user's underlying persistent preferences.
        """
        raw = self.get_all()
        master = raw.get("master_alert_system", True)
        quiet = raw.get("quiet_mode", False)
        alert_override = master and not quiet

        return {
            "master_alert_system": master,
            "success_sound": raw.get("success_sound", True) and alert_override,
            "failure_sound": raw.get("failure_sound", True) and alert_override,
            "desktop_notification": raw.get("desktop_notification", True) and alert_override,
            "failure_intelligence": raw.get("failure_intelligence", True),
            "job_summary": raw.get("job_summary", True),
            "quiet_mode": quiet
        }

    # ── Alert Evaluation Helpers ──────────────────────────────────────────────
    def is_success_sound_allowed(self) -> bool:
        """Check if success audio should play."""
        all_s = self.get_all()
        if not all_s.get("master_alert_system", True):
            return False
        if all_s.get("quiet_mode", False):
            return False
        return all_s.get("success_sound", True)

    def is_failure_sound_allowed(self) -> bool:
        """Check if failure/error audio should play."""
        all_s = self.get_all()
        if not all_s.get("master_alert_system", True):
            return False
        if all_s.get("quiet_mode", False):
            return False
        return all_s.get("failure_sound", True)

    def is_notification_allowed(self) -> bool:
        """Check if Windows desktop toast notifications should appear."""
        all_s = self.get_all()
        if not all_s.get("master_alert_system", True):
            return False
        if all_s.get("quiet_mode", False):
            return False
        return all_s.get("desktop_notification", True)

    def is_intelligence_enabled(self) -> bool:
        """Check if failure intelligence diagnosis is enabled."""
        return self.get("failure_intelligence", True)

    def is_summary_enabled(self) -> bool:
        """Check if job summary generation is enabled."""
        return self.get("job_summary", True)

# Global singleton configuration instance
config = ConfigManager()

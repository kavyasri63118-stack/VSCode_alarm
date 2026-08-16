"""
Centralized Resource Path Resolver for Code Alarm V2.
Guarantees correct resolution of assets, web dashboard files, and audio assets
in both development mode and PyInstaller bundled executable environments.
"""

import os
import sys
from pathlib import Path

def get_base_dir() -> Path:
    """
    Get root base directory of Code Alarm.
    Handles PyInstaller bundled _MEIPASS and development filesystem layouts.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running inside PyInstaller bundled executable
        return Path(sys._MEIPASS)
    
    # Development layout: python/code_alarm/resources.py -> root is 3 levels up
    dev_root = Path(__file__).resolve().parent.parent.parent
    if (dev_root / "web_dashboard").exists():
        return dev_root
    
    # Fallback to current module parent directory
    return Path(__file__).resolve().parent

def get_dashboard_dir() -> Path:
    """Resolve directory containing web_dashboard assets (index.html, style.css, app.js)."""
    base = get_base_dir()
    candidate = base / "web_dashboard"
    if candidate.exists():
        return candidate
    return base

def get_sounds_dir() -> Path:
    """Resolve directory containing .wav audio assets."""
    base = get_base_dir()
    # Check bundled sounds path
    candidate = base / "sounds"
    if candidate.exists():
        return candidate
    candidate = base / "python" / "code_alarm" / "sounds"
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parent / "sounds"

def get_icon_path(fmt: str = "ico") -> Path:
    """Resolve application icon (.ico or .png)."""
    base = get_base_dir()
    fname = f"code_alarm.{fmt}"
    candidate = base / "assets" / fname
    if candidate.exists():
        return candidate
    candidate = base / fname
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parent.parent.parent / "assets" / fname

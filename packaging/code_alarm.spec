# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

SPEC_ROOT = Path(os.path.abspath(".")).resolve()
PYTHON_PKG = SPEC_ROOT / "python"

datas = [
    (str(SPEC_ROOT / "web_dashboard"), "web_dashboard"),
    (str(PYTHON_PKG / "code_alarm" / "sounds"), "sounds"),
    (str(SPEC_ROOT / "assets" / "code_alarm.ico"), "assets"),
    (str(SPEC_ROOT / "assets" / "code_alarm.png"), "assets"),
]

hiddenimports = [
    "pystray",
    "pystray._win32",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "webview",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "clr_loader",
    "pythonnet",
    "sqlite3",
    "winreg",
    "http.server",
    "socketserver",
    "winsound",
    "code_alarm",
    "code_alarm.storage",
    "code_alarm.config",
    "code_alarm.intelligence",
    "code_alarm.summary",
    "code_alarm.runner",
    "code_alarm.laptop_alerts",
    "code_alarm.resources",
    "code_alarm.app_lifecycle",
    "code_alarm.tray",
    "code_alarm.desktop",
    "code_alarm.cli",
]

# ── 1. Desktop GUI App Analysis ──────────────────────────────────────────────
a_gui = Analysis(
    [str(SPEC_ROOT / 'desktop_app.py')],
    pathex=[str(SPEC_ROOT), str(PYTHON_PKG)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name='CodeAlarm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(SPEC_ROOT / "assets" / "code_alarm.ico")
)

# ── 2. Terminal CLI App Analysis ─────────────────────────────────────────────
a_cli = Analysis(
    [str(SPEC_ROOT / 'cli_app.py')],
    pathex=[str(SPEC_ROOT), str(PYTHON_PKG)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_cli = PYZ(a_cli.pure, a_cli.zipped_data, cipher=block_cipher)

exe_cli = EXE(
    pyz_cli,
    a_cli.scripts,
    [],
    exclude_binaries=True,
    name='code-alarm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(SPEC_ROOT / "assets" / "code_alarm.ico")
)

# ── Collect into unified distribution directory ──────────────────────────────
coll = COLLECT(
    exe_gui,
    a_gui.binaries,
    a_gui.zipfiles,
    a_gui.datas,
    exe_cli,
    a_cli.scripts,
    a_cli.binaries,
    a_cli.zipfiles,
    a_cli.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CodeAlarm'
)

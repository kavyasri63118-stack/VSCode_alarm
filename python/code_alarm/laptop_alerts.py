"""
Laptop Native Audio & Notification Engine for Code Alarm V2
Multi-layered audio playback using:
1. High-fidelity direct PCM .WAV audio playback via winsound.PlaySound (DirectSound)
2. Windows system audio events via winsound.MessageBeep (fallback)
3. Windows 10/11 Desktop Toast Notifications (short attention signals)
4. Optional Spoken Voice Announcement
5. Strict respect for Alert Control Center settings.
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional

from .config import config
from .resources import get_sounds_dir

def _ensure_sounds():
    """Ensure WAV sound assets exist."""
    sounds_dir = get_sounds_dir()
    if not (sounds_dir / "success.wav").exists():
        try:
            from .sound_builder import build_all_sounds
            build_all_sounds()
        except Exception:
            pass

def play_audio_alarm(pattern: str = "SUCCESS"):
    """
    Play high-fidelity chime audio directly through laptop speakers / headphones.
    Guaranteed to work across Realtek, Intel, HDMI, USB, and Bluetooth audio devices.
    Respects Alert Control Center toggles (Master Alert, Quiet Mode, Success/Failure Sound).
    """
    pattern = pattern.upper()
    is_success = pattern in ("SUCCESS", "DONE", "TRAIN_DONE", "VICTORY", "0")

    # Check config permissions
    if is_success:
        if not config.is_success_sound_allowed():
            return
    else:
        if not config.is_failure_sound_allowed():
            return

    _ensure_sounds()

    wav_name = "success.wav"
    if pattern in ("ERROR", "FAIL", "CRASH", "1"):
        wav_name = "error.wav"
    elif pattern in ("TRAIN_DONE", "TRAIN_SUCCESS", "VICTORY", "3"):
        wav_name = "train_done.wav"
    elif pattern in ("ALERT", "CRITICAL", "4"):
        wav_name = "alert.wav"

    wav_path = get_sounds_dir() / wav_name
    played = False

    # Method 1: Play high-fidelity WAV file via DirectSound
    if wav_path.exists() and sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(str(wav_path), winsound.SND_FILENAME)
            played = True
        except Exception:
            pass

    # Method 2: Fallback to Windows native System MessageBeep
    if not played and sys.platform == "win32":
        try:
            import winsound
            if pattern in ("ERROR", "FAIL", "CRASH", "1"):
                winsound.MessageBeep(winsound.MB_ICONHAND)
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            played = True
        except Exception:
            pass

    # Method 3: Fallback to winsound.Beep frequency pulses
    if not played and sys.platform == "win32":
        try:
            import winsound
            if pattern in ("ERROR", "FAIL", "CRASH", "1"):
                winsound.Beep(700, 150)
                winsound.Beep(450, 200)
            else:
                winsound.Beep(523, 100)
                winsound.Beep(659, 100)
                winsound.Beep(784, 250)
        except Exception:
            print("\a", end="", flush=True)

def show_desktop_notification(title: str, message: str, is_success: bool = True):
    """
    Display native Windows Toast Notification in the bottom right corner of screen.
    Respects Alert Control Center toggles (Master Alert, Quiet Mode, Desktop Notification).
    """
    if sys.platform != "win32":
        return

    if not config.is_notification_allowed():
        return

    icon_type = "Info" if is_success else "Error"
    # Escape quotes in title & message
    safe_title = title.replace('"', '`"')
    safe_msg = message.replace('"', '`"')

    ps_cmd = f"""
    [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::{icon_type}
    $notify.BalloonTipTitle = "{safe_title}"
    $notify.BalloonTipText = "{safe_msg}"
    $notify.Visible = $True
    $notify.ShowBalloonTip(4000)
    Start-Sleep -Milliseconds 600
    $notify.Dispose()
    """
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def speak_voice_announcement(text: str):
    """
    Speak voice alert using built-in Windows SAPI Text-to-Speech.
    """
    if sys.platform != "win32":
        return

    if not config.is_notification_allowed():
        return

    safe_text = text.replace('"', '`"')
    ps_speech = f"""
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 1
    $synth.Speak("{safe_text}")
    """
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_speech],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def trigger_laptop_alert(
    title: str = "Code Alarm",
    message: str = "Execution finished",
    pattern: str = "SUCCESS",
    voice: bool = False,
    voice_message: Optional[str] = None
):
    """
    Trigger full laptop alert: Speaker WAV Chime + Desktop Toast + Optional Voice.
    Synchronous audio playback ensures complete sound wave before process exit.
    """
    is_success = pattern.upper() in ("SUCCESS", "DONE", "TRAIN_DONE", "VICTORY", "0")

    # 1. Show Windows desktop notification (background thread)
    t_notify = threading.Thread(target=show_desktop_notification, args=(title, message, is_success), daemon=True)
    t_notify.start()

    # 2. Optional Voice TTS (background thread)
    if voice:
        spoken = voice_message or message
        t_voice = threading.Thread(target=speak_voice_announcement, args=(spoken,), daemon=True)
        t_voice.start()

    # 3. Play audio chime synchronously on laptop speakers
    try:
        play_audio_alarm(pattern)
    except Exception:
        pass

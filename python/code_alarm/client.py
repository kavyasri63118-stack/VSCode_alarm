"""
Serial client with automatic USB port discovery, caching, and hardware signaling.
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Optional, List, Tuple
from .audio_fallback import play_software_fallback

try:
    import serial
    import serial.tools.list_ports
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False

CONFIG_PATH = Path.home() / ".code_alarm_config.json"
DEFAULT_BAUD = 115200

class CodeAlarmClient:
    def __init__(self, port: Optional[str] = None, baud: int = DEFAULT_BAUD, fallback_audio: bool = True, timeout: float = 0.5):
        self.port = port
        self.baud = baud
        self.fallback_audio = fallback_audio
        self.timeout = timeout
        self.ser: Optional["serial.Serial"] = None
        self._connected = False

    def _load_cached_port(self) -> Optional[str]:
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("last_known_port")
            except Exception:
                pass
        return None

    def _save_cached_port(self, port: str):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({"last_known_port": port, "updated_at": time.time()}, f)
        except Exception:
            pass

    @classmethod
    def list_ports(cls) -> List[Tuple[str, str]]:
        """Return list of (port, description) for all connected COM devices."""
        if not HAS_PYSERIAL:
            return []
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]

    def _try_handshake(self, port_name: str) -> bool:
        """Send PING to port and verify PONG:CODE_ALARM response."""
        try:
            with serial.Serial(port_name, self.baud, timeout=0.3, write_timeout=0.3) as s:
                # Give Arduino Uno/Nano a moment to reset DTR on connection
                time.sleep(0.1)
                s.reset_input_buffer()
                s.write(b"PING\n")
                s.flush()
                
                start_t = time.time()
                while time.time() - start_t < 0.4:
                    if s.in_waiting:
                        line = s.readline().decode("utf-8", errors="ignore").strip()
                        if "PONG:CODE_ALARM" in line or "PONG" in line:
                            return True
                    time.sleep(0.02)
        except Exception:
            return False
        return False

    def find_device_port(self) -> Optional[str]:
        """Automatically find the COM port connected to the Code Alarm hardware."""
        if not HAS_PYSERIAL:
            return None

        # 1. Check explicitly specified port
        if self.port:
            if self._try_handshake(self.port):
                self._save_cached_port(self.port)
                return self.port
            return self.port  # Return anyway if user explicitly requested it

        # 2. Check cached port first for instant (<20ms) connection
        cached = self._load_cached_port()
        if cached:
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            if cached in available_ports and self._try_handshake(cached):
                return cached

        # 3. Scan all active COM ports
        for p in serial.tools.list_ports.comports():
            # Skip standard Bluetooth COM ports to avoid lag
            desc_lower = p.description.lower()
            if "bluetooth" in desc_lower or "bth" in desc_lower:
                continue
            if self._try_handshake(p.device):
                self._save_cached_port(p.device)
                return p.device

        # 4. Fallback heuristic: check common USB-Serial descriptions (CH340, CP210x, Arduino, FTDI)
        for p in serial.tools.list_ports.comports():
            desc_lower = p.description.lower()
            if any(chip in desc_lower for chip in ("ch340", "cp210", "arduino", "ftdi", "usb serial", "usb-serial")):
                self._save_cached_port(p.device)
                return p.device

        # 5. If only 1 COM port exists on machine, assume it's our device
        ports = serial.tools.list_ports.comports()
        if len(ports) == 1:
            return ports[0].device

        return None

    def send_signal(self, command: str) -> bool:
        """
        Send a signal to the hardware alarm (e.g. 'SUCCESS', 'ERROR', 'TRAIN_DONE', 'ALERT', 'STOP').
        Falls back to laptop speaker beeps if hardware is disconnected.
        """
        command = command.strip().upper()
        hardware_success = False

        if HAS_PYSERIAL:
            resolved_port = self.find_device_port()
            if resolved_port:
                try:
                    with serial.Serial(resolved_port, self.baud, timeout=self.timeout, write_timeout=self.timeout) as s:
                        # Ensure DTR is ready
                        time.sleep(0.05)
                        msg = f"{command}\n".encode("utf-8")
                        s.write(msg)
                        s.flush()
                        time.sleep(0.05)
                        hardware_success = True
                except Exception as e:
                    hardware_success = False

        # If hardware is not connected or failed, play audio fallback on laptop
        if not hardware_success and self.fallback_audio:
            play_software_fallback(command, async_mode=True)

        return hardware_success

    def success(self):
        """Trigger single success beep (Exit Code 0)."""
        return self.send_signal("SUCCESS")

    def error(self):
        """Trigger error warning beeps (Exit Code != 0 / Crash)."""
        return self.send_signal("ERROR")

    def train_done(self):
        """Trigger 3 victory beeps (ML / Long Run completed)."""
        return self.send_signal("TRAIN_DONE")

    def alert(self):
        """Trigger rapid continuous alert."""
        return self.send_signal("ALERT")

    def stop(self):
        """Silence any ongoing alarm."""
        return self.send_signal("STOP")

    def test(self):
        """Run diagnostic test sound."""
        return self.send_signal("TEST")

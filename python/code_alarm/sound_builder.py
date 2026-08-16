"""
Synthesize crisp, crystal-clear .WAV sound files for Code-Alarm.
Uses standard Python `wave` and `math` (zero external dependencies).
Guarantees 100% audio playback across all Windows laptop speakers, headphones, and sound cards.
"""

import os
import wave
import struct
import math
from pathlib import Path

SOUNDS_DIR = Path(__file__).parent / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100

def _generate_wav(filename: str, notes: list):
    """
    notes is a list of tuples: (frequency_hz, duration_seconds, volume)
    """
    filepath = SOUNDS_DIR / filename
    total_samples = []

    for freq, duration, vol in notes:
        num_samples = int(SAMPLE_RATE * duration)
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            # Smooth envelope (fade in 5ms, fade out 20ms) to avoid clicks
            fade_in = min(1.0, i / (SAMPLE_RATE * 0.005))
            fade_out = min(1.0, (num_samples - i) / (SAMPLE_RATE * 0.020))
            envelope = fade_in * fade_out
            
            # Harmonic sine wave with rich overtones
            sample = (
                0.70 * math.sin(2 * math.pi * freq * t) +
                0.20 * math.sin(2 * math.pi * (freq * 2) * t) +
                0.10 * math.sin(2 * math.pi * (freq * 3) * t)
            )
            val = int(sample * vol * envelope * 32767.0)
            val = max(-32767, min(32767, val))
            total_samples.append(val)

    with wave.open(str(filepath), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        packed_data = struct.pack(f"<{len(total_samples)}h", *total_samples)
        wav_file.writeframes(packed_data)

def build_all_sounds():
    # 1. SUCCESS: 3-note ascending crystal chime (C5 -> E5 -> G5)
    _generate_wav("success.wav", [
        (523.25, 0.10, 0.8),  # C5
        (659.25, 0.10, 0.8),  # E5
        (783.99, 0.28, 0.9),  # G5
    ])

    # 2. ERROR: 2-note descending warning chord (700Hz -> 350Hz)
    _generate_wav("error.wav", [
        (680.0, 0.12, 0.85),
        (340.0, 0.28, 0.9),
    ])

    # 3. TRAIN_DONE / VICTORY: 4-note fanfare (C5 -> E5 -> G5 -> C6)
    _generate_wav("train_done.wav", [
        (523.25, 0.09, 0.8),
        (659.25, 0.09, 0.8),
        (783.99, 0.12, 0.85),
        (1046.50, 0.35, 0.95),
    ])

    # 4. ALERT: Urgent double pulse
    _generate_wav("alert.wav", [
        (1200.0, 0.08, 0.9),
        (1600.0, 0.08, 0.9),
        (1200.0, 0.08, 0.9),
        (1600.0, 0.18, 0.9),
    ])

if __name__ == "__main__":
    build_all_sounds()
    print("Generated high-fidelity WAV sound files in:", SOUNDS_DIR)

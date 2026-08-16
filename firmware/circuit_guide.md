# 🔌 Minimal 2-Wire Hardware Wiring Guide

This is designed for a fast, minimalist setup right on your desk or laptop with **zero extra components** (no breadboard, no resistors, no LEDs required).

---

## 🛠️ What You Need
1. **Microcontroller**: Arduino Uno, Nano, Pro Micro, or ESP32 / ESP8266.
2. **Active Buzzer**: Standard 5V or 3.3V active buzzer (the ones with a small sticker on top).
3. **2 Female-to-Male or Female-to-Female Jumper Wires** (or directly plug into Arduino header).
4. **USB Cable** to plug into your laptop.

---

## ⚡ 1. Arduino Uno / Nano Wiring (Only 2 Pins!)

```text
 ┌──────────────────────────────────────────────┐
 │               ARDUINO UNO / NANO             │
 │                                              │
 │                 [ D8 ] ────────── (+) Long Pin (Positive)
 │                                        ┌─────────┐
 │                                        │ ACTIVE  │
 │                                        │ BUZZER  │
 │                 [ GND ] ───────── (-) Short Pin (Ground)
 │                                        └─────────┘
 │                                              │
 │   [ USB-C / Mini-B / Type-B ] ═══════════════╪═════> Laptop USB Port
 └──────────────────────────────────────────────┘
```

### Pin Table:
| Buzzer Pin | Arduino Pin | Note |
|---|---|---|
| **`+` (Long leg / labeled +)** | **`D8`** | Digital Output Pin 8 |
| **`-` (Short leg / GND)** | **`GND`** | Ground |

---

## ⚡ 2. ESP32 / NodeMCU Wiring

```text
 ┌──────────────────────────────────────────────┐
 │                    ESP32                     │
 │                                              │
 │                [ GPIO 18 ] ────── (+) Positive
 │                                        ┌─────────┐
 │                                        │ ACTIVE  │
 │                                        │ BUZZER  │
 │                 [ GND ] ───────── (-) Ground
 │                                        └─────────┘
 │                                              │
 │              [ Micro USB / Type-C ] ═════════╪═════> Laptop USB Port
 └──────────────────────────────────────────────┘
```

### Pin Table:
| Buzzer Pin | ESP32 Pin | Note |
|---|---|---|
| **`+` (Positive)** | **`GPIO 18`** (Pin D18) | Digital Output |
| **`-` (Ground)** | **`GND`** | Ground |

---

## 🚀 How to Flash the Firmware

1. Open **Arduino IDE** (or VS Code with Arduino / PlatformIO extension).
2. Open `firmware/code_alarm_firmware/code_alarm_firmware.ino`.
3. Select your Board:
   - **Tools > Board > Arduino AVR Boards > Arduino Uno / Nano** (or ESP32 Dev Module).
4. Select the COM Port:
   - **Tools > Port > COMx** (the one that appears when you plug in the USB).
5. Click **Upload** (Arrow icon).
6. **Done!** The buzzer will make a quick 50ms startup chirp to confirm it is powered and ready.

---

## 💡 Active vs Passive Buzzer:
- **Active Buzzer (Recommended)**: Has an internal oscillator. When D8 goes `HIGH`, it beeps loudly on its own.
- **Passive Buzzer**: Needs frequency waves (`tone()`). If you have a passive buzzer, simply change `#define IS_ACTIVE_BUZZER 0` at line 20 in `code_alarm_firmware.ino`.

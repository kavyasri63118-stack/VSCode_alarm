/*
 * ═══════════════════════════════════════════════════════════════════════════
 *  LAPTOP CODE-COMPLETION ALARM - FIRMWARE
 * ═══════════════════════════════════════════════════════════════════════════
 *  Hardware Requirements:
 *    - Arduino Uno / Nano / Mega / Pro Mini OR ESP32 / ESP8266 / RP2040
 *    - 1x Active Buzzer (5V or 3.3V) OR Passive Buzzer
 *    - USB Cable connected to Laptop
 *
 *  Minimal Wiring (Only 2 wires!):
 *    - Buzzer (+) Pin -> Arduino Pin D8 (or ESP32 GPIO 18)
 *    - Buzzer (-) Pin -> Arduino GND
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ── PIN CONFIGURATION ────────────────────────────────────────────────────────
#if defined(ESP32) || defined(ESP8266)
  #define BUZZER_PIN 18     // Change to your chosen GPIO if using ESP32
#else
  #define BUZZER_PIN 8      // Digital Pin 8 on Arduino Uno / Nano
#endif

// Set to 1 for Active Buzzer (digital HIGH/LOW), 0 for Passive Buzzer (frequency tones)
#define IS_ACTIVE_BUZZER 1

// ── SERIAL CONFIGURATION ─────────────────────────────────────────────────────
#define SERIAL_BAUD 115200

// ── SOUND PATTERNS ───────────────────────────────────────────────────────────
enum AlarmPattern {
  PATTERN_IDLE = 0,
  PATTERN_SUCCESS,     // 1 clean beep (code ran successfully)
  PATTERN_ERROR,       // 2 low/quick warning beeps (exception/syntax error)
  PATTERN_TRAIN_DONE,  // 3 victory beeps (long run/ML training complete)
  PATTERN_ALERT,       // Continuous alert beeps (critical failure)
  PATTERN_TEST         // Quick sequence test
};

AlarmPattern currentPattern = PATTERN_IDLE;
int patternStep = 0;
unsigned long stepStartTime = 0;
bool isBuzzing = false;
int alertCyclesLeft = 0;

// ── BUZZER CONTROL HELPERS ───────────────────────────────────────────────────
void buzzerOn(int frequency = 2400) {
#if IS_ACTIVE_BUZZER
  digitalWrite(BUZZER_PIN, HIGH);
#else
  tone(BUZZER_PIN, frequency);
#endif
  isBuzzing = true;
}

void buzzerOff() {
#if IS_ACTIVE_BUZZER
  digitalWrite(BUZZER_PIN, LOW);
#else
  noTone(BUZZER_PIN);
#endif
  isBuzzing = false;
}

void startPattern(AlarmPattern pattern) {
  currentPattern = pattern;
  patternStep = 0;
  stepStartTime = millis();
  
  if (pattern == PATTERN_ALERT) {
    alertCyclesLeft = 10; // Beep 10 times for continuous alert
  }
}

void stopAlarm() {
  buzzerOff();
  currentPattern = PATTERN_IDLE;
  patternStep = 0;
}

// ── NON-BLOCKING PATTERN RUNNER ──────────────────────────────────────────────
void updateAlarm() {
  if (currentPattern == PATTERN_IDLE) return;

  unsigned long elapsed = millis() - stepStartTime;

  switch (currentPattern) {
    // -------------------------------------------------------------------------
    // SUCCESS: 1 Beep (250ms ON, then OFF)
    // -------------------------------------------------------------------------
    case PATTERN_SUCCESS:
      if (patternStep == 0) {
        buzzerOn(2600); // 2.6kHz tone
        patternStep = 1;
        stepStartTime = millis();
      } else if (patternStep == 1 && elapsed >= 250) {
        buzzerOff();
        currentPattern = PATTERN_IDLE;
      }
      break;

    // -------------------------------------------------------------------------
    // ERROR: 2 Warning Beeps (120ms ON, 80ms OFF, 250ms ON)
    // -------------------------------------------------------------------------
    case PATTERN_ERROR:
      if (patternStep == 0) {
        buzzerOn(1800); // Low warning tone
        patternStep = 1;
        stepStartTime = millis();
      } else if (patternStep == 1 && elapsed >= 120) {
        buzzerOff();
        patternStep = 2;
        stepStartTime = millis();
      } else if (patternStep == 2 && elapsed >= 80) {
        buzzerOn(1400); // Lower tone
        patternStep = 3;
        stepStartTime = millis();
      } else if (patternStep == 3 && elapsed >= 250) {
        buzzerOff();
        currentPattern = PATTERN_IDLE;
      }
      break;

    // -------------------------------------------------------------------------
    // TRAIN_DONE: 3 Victory Beeps (100ms ON, 60ms OFF x 3)
    // -------------------------------------------------------------------------
    case PATTERN_TRAIN_DONE:
      if (patternStep == 0) {
        buzzerOn(2000);
        patternStep = 1;
        stepStartTime = millis();
      } else if (patternStep == 1 && elapsed >= 100) {
        buzzerOff();
        patternStep = 2;
        stepStartTime = millis();
      } else if (patternStep == 2 && elapsed >= 60) {
        buzzerOn(2400);
        patternStep = 3;
        stepStartTime = millis();
      } else if (patternStep == 3 && elapsed >= 100) {
        buzzerOff();
        patternStep = 4;
        stepStartTime = millis();
      } else if (patternStep == 4 && elapsed >= 60) {
        buzzerOn(2900);
        patternStep = 5;
        stepStartTime = millis();
      } else if (patternStep == 5 && elapsed >= 300) {
        buzzerOff();
        currentPattern = PATTERN_IDLE;
      }
      break;

    // -------------------------------------------------------------------------
    // ALERT: Continuous Rapid Alert Beeps
    // -------------------------------------------------------------------------
    case PATTERN_ALERT:
      if (patternStep == 0) {
        buzzerOn(3000);
        patternStep = 1;
        stepStartTime = millis();
      } else if (patternStep == 1 && elapsed >= 150) {
        buzzerOff();
        patternStep = 2;
        stepStartTime = millis();
      } else if (patternStep == 2 && elapsed >= 100) {
        alertCyclesLeft--;
        if (alertCyclesLeft > 0) {
          patternStep = 0; // Repeat beep
        } else {
          currentPattern = PATTERN_IDLE;
        }
      }
      break;

    // -------------------------------------------------------------------------
    // TEST: Diagnostic sequence (Success -> Error -> Victory)
    // -------------------------------------------------------------------------
    case PATTERN_TEST:
      if (patternStep == 0) {
        buzzerOn(2400);
        patternStep = 1;
        stepStartTime = millis();
      } else if (patternStep == 1 && elapsed >= 200) {
        buzzerOff();
        patternStep = 2;
        stepStartTime = millis();
      } else if (patternStep == 2 && elapsed >= 200) {
        buzzerOn(1800);
        patternStep = 3;
        stepStartTime = millis();
      } else if (patternStep == 3 && elapsed >= 200) {
        buzzerOff();
        currentPattern = PATTERN_IDLE;
      }
      break;

    default:
      buzzerOff();
      currentPattern = PATTERN_IDLE;
      break;
  }
}

// ── SERIAL COMMAND PROCESSOR ─────────────────────────────────────────────────
void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd.length() == 0) return;

  if (cmd == "PING") {
    // Handshake for automatic USB COM port detection
    Serial.println("PONG:CODE_ALARM_V1");
  } 
  else if (cmd == "SUCCESS" || cmd == "DONE" || cmd == "1") {
    startPattern(PATTERN_SUCCESS);
    Serial.println("ACK:SUCCESS");
  } 
  else if (cmd == "ERROR" || cmd == "FAIL" || cmd == "CRASH" || cmd == "2") {
    startPattern(PATTERN_ERROR);
    Serial.println("ACK:ERROR");
  } 
  else if (cmd == "TRAIN_DONE" || cmd == "TRAIN_SUCCESS" || cmd == "3") {
    startPattern(PATTERN_TRAIN_DONE);
    Serial.println("ACK:TRAIN_DONE");
  } 
  else if (cmd == "ALERT" || cmd == "CRITICAL" || cmd == "4") {
    startPattern(PATTERN_ALERT);
    Serial.println("ACK:ALERT");
  } 
  else if (cmd == "TEST") {
    startPattern(PATTERN_TEST);
    Serial.println("ACK:TEST");
  } 
  else if (cmd == "STOP" || cmd == "MUTE" || cmd == "0") {
    stopAlarm();
    Serial.println("ACK:STOP");
  } 
  else {
    Serial.print("ERR:UNKNOWN_COMMAND:");
    Serial.println(cmd);
  }
}

// ── SETUP & MAIN LOOP ────────────────────────────────────────────────────────
void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  buzzerOff();

  Serial.begin(SERIAL_BAUD);
  
  // Quick startup confirmation blip (50ms)
  buzzerOn(2400);
  delay(50);
  buzzerOff();
}

void loop() {
  // Read incoming commands over USB Serial
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    processCommand(input);
  }

  // Non-blocking update of active beep patterns
  updateAlarm();
}

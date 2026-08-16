#include <Arduino.h>
#include <esp_arduino_version.h>

// SpectraRover four-motor controller for ESP32 DevKit-style boards.
// IMPORTANT: verify your exact board pinout and motor-driver wiring before use.
// The controller boots DISARMED and stops on command timeout.

struct MotorPins {
  int in1;
  int in2;
  int pwm;
  int channel;
};

const MotorPins FL{13, 14, 25, 0};
const MotorPins FR{16, 17, 26, 1};
const MotorPins RL{18, 19, 27, 2};
const MotorPins RR{21, 22, 32, 3};
const int STBY_PIN = 33;  // Tie both TB6612 STBY pins together here.

const unsigned long WATCHDOG_MS = 500;
const int PWM_FREQ = 20000;
const int PWM_BITS = 8;
const int PWM_MAX = (1 << PWM_BITS) - 1;

bool armed = false;
unsigned long lastCommandMs = 0;
String inputLine;

void attachPwm(const MotorPins &m) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(m.pwm, PWM_FREQ, PWM_BITS);
#else
  ledcSetup(m.channel, PWM_FREQ, PWM_BITS);
  ledcAttachPin(m.pwm, m.channel);
#endif
}

void writePwm(const MotorPins &m, int duty) {
  duty = constrain(duty, 0, PWM_MAX);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(m.pwm, duty);
#else
  ledcWrite(m.channel, duty);
#endif
}

void stopMotor(const MotorPins &m) {
  digitalWrite(m.in1, LOW);
  digitalWrite(m.in2, LOW);
  writePwm(m, 0);
}

void stopAll() {
  stopMotor(FL);
  stopMotor(FR);
  stopMotor(RL);
  stopMotor(RR);
}

void setMotor(const MotorPins &m, float command) {
  command = constrain(command, -1.0f, 1.0f);
  if (!armed || fabs(command) < 0.001f) {
    stopMotor(m);
    return;
  }

  const bool forward = command > 0.0f;
  digitalWrite(m.in1, forward ? HIGH : LOW);
  digitalWrite(m.in2, forward ? LOW : HIGH);
  writePwm(m, (int)(fabs(command) * PWM_MAX));
}

void disarm() {
  armed = false;
  stopAll();
  digitalWrite(STBY_PIN, LOW);
}

void arm() {
  stopAll();
  digitalWrite(STBY_PIN, HIGH);
  armed = true;
  lastCommandMs = millis();
}

void handleLine(String line) {
  line.trim();
  if (line.length() == 0) return;

  if (line == "ARM") {
    arm();
    Serial.println("OK ARMED");
    return;
  }
  if (line == "DISARM") {
    disarm();
    Serial.println("OK DISARMED");
    return;
  }
  if (line == "STOP") {
    stopAll();
    lastCommandMs = millis();
    Serial.println("OK STOPPED");
    return;
  }
  if (line == "PING") {
    Serial.println(armed ? "PONG ARMED" : "PONG DISARMED");
    return;
  }

  float fl, fr, rl, rr;
  if (sscanf(line.c_str(), "WHEELS %f %f %f %f", &fl, &fr, &rl, &rr) == 4) {
    if (!armed) {
      Serial.println("ERR NOT_ARMED");
      return;
    }
    setMotor(FL, fl);
    setMotor(FR, fr);
    setMotor(RL, rl);
    setMotor(RR, rr);
    lastCommandMs = millis();
    Serial.println("OK WHEELS");
    return;
  }

  Serial.println("ERR UNKNOWN_COMMAND");
}

void setup() {
  Serial.begin(115200);
  inputLine.reserve(128);

  const MotorPins motors[] = {FL, FR, RL, RR};
  for (const MotorPins &m : motors) {
    pinMode(m.in1, OUTPUT);
    pinMode(m.in2, OUTPUT);
    attachPwm(m);
  }
  pinMode(STBY_PIN, OUTPUT);
  disarm();
  Serial.println("SPECTRAROVER MOTOR CONTROLLER READY DISARMED");
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      handleLine(inputLine);
      inputLine = "";
    } else if (c != '\r' && inputLine.length() < 120) {
      inputLine += c;
    }
  }

  if (armed && (millis() - lastCommandMs > WATCHDOG_MS)) {
    stopAll();
    disarm();
    Serial.println("WATCHDOG DISARMED");
  }
}

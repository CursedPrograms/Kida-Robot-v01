#include "Adafruit_VL53L0X.h"
#include <Servo.h>
#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
#include <avr/power.h>
#include <Wire.h>
#endif

// ===============================================
// CONFIGURATION CONSTANTS
// ===============================================
namespace Config {

  constexpr uint8_t SERVO_PIN = 10;

  constexpr uint8_t ULTRASONIC0_TRIG = A1;
  constexpr uint8_t ULTRASONIC0_ECHO = A0;
  constexpr uint8_t ULTRASONIC1_TRIG = A2;
  constexpr uint8_t ULTRASONIC1_ECHO = A3;

  constexpr uint8_t BUZZER_PIN = 8;
  constexpr uint8_t BUTTON_PIN = 2;

  constexpr uint8_t MOTOR_RIGHT_PWM = 3;
  constexpr uint8_t MOTOR_RIGHT_DIR1 = 4;
  constexpr uint8_t MOTOR_RIGHT_DIR2 = 5;
  constexpr uint8_t MOTOR_LEFT_PWM = 6;
  constexpr uint8_t MOTOR_LEFT_DIR1 = 7;
  constexpr uint8_t MOTOR_LEFT_DIR2 = 9;

  constexpr uint8_t STRIP1_PIN = 13;
  constexpr uint8_t STRIP2_PIN = 12;
  constexpr uint8_t NUM_PIXELS = 8;

  constexpr uint8_t DEFAULT_MOTOR_SPEED = 200;
  constexpr uint16_t SERIAL_BAUD_RATE = 9600;
  constexpr uint8_t SERVO_CENTER_POSITION = 90;
  constexpr uint16_t STARTUP_TONE_FREQ = 440;
  constexpr uint16_t MODE_SWITCH_TONE_FREQ = 1000;
}

// ===============================================
// TYPE DEFINITIONS
// ===============================================
enum class MotorDirection : uint8_t { STOP = 0, FORWARD, BACKWARD, LEFT, RIGHT };
enum class LightPattern : uint8_t { OFF = 0, ON, STROBE, CYCLE, RAINBOW, GREEN };

struct RobotState {
  MotorDirection currentDirection = MotorDirection::STOP;
  uint8_t motorSpeed = Config::DEFAULT_MOTOR_SPEED;
  bool buttonPressed = false;
  bool systemReady = false;
};

struct SensorReadings {
  int laserDistance = -1;
  long ultrasonic0Distance = -1;
  long ultrasonic1Distance = -1;
  bool buttonState = false;
};

// ===============================================
// HARDWARE INSTANCES
// ===============================================
Adafruit_VL53L0X laserSensor;
Servo robotServo;
Adafruit_NeoPixel strip1(Config::NUM_PIXELS, Config::STRIP1_PIN, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel strip2(Config::NUM_PIXELS, Config::STRIP2_PIN, NEO_GRB + NEO_KHZ800);

// ===============================================
// GLOBAL STATE
// ===============================================
RobotState robotState;

// ========================
// NON-BLOCKING TIMERS
// ========================
unsigned long lastSensorPrint = 0;
unsigned long sensorPrintInterval = 200; // ms
unsigned long lastStrobe = 0;
unsigned long strobeInterval = 100;      // ms
unsigned long rainbowIndex = 0;

// ===============================================
// HARDWARE FUNCTIONS
// ===============================================
bool initializeLaserSensor() {
  if (!laserSensor.begin()) {
    Serial.println(F("ERROR: VL53L0X initialization failed"));
    return false;
  }
  Serial.println(F("VL53L0X sensor ready"));
  return true;
}

void initializeServo() {
  robotServo.attach(Config::SERVO_PIN);
  robotServo.write(Config::SERVO_CENTER_POSITION);
  delay(500);

  const uint8_t testPositions[] = {45, 135, 90};
  for (uint8_t pos : testPositions) {
    robotServo.write(pos);
    delay(500);
  }
}


long readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 30000); // max 30ms
  return duration * 0.034 / 2; // cm
}

long ScanForObstacles_Left() {
  robotServo.write(45);  // Move servo to left
  delay(500);
  long distance = readUltrasonic(Config::ULTRASONIC1_TRIG, Config::ULTRASONIC1_ECHO);
  Serial.print("LEFT:"); Serial.println(distance); // send reading
  robotServo.write(Config::SERVO_CENTER_POSITION); // Return to center
  delay(500);
  return distance;
}

long ScanForObstacles_Right() {
  robotServo.write(135);  // Move servo to right
  delay(500);
  long distance = readUltrasonic(Config::ULTRASONIC1_TRIG, Config::ULTRASONIC1_ECHO);
  Serial.print("RIGHT:"); Serial.println(distance); // send reading
  robotServo.write(Config::SERVO_CENTER_POSITION); // Return to center
  delay(500);
  return distance;
}

  

void initializeMotors() {
  pinMode(Config::MOTOR_RIGHT_PWM, OUTPUT);
  pinMode(Config::MOTOR_RIGHT_DIR1, OUTPUT);
  pinMode(Config::MOTOR_RIGHT_DIR2, OUTPUT);
  pinMode(Config::MOTOR_LEFT_PWM, OUTPUT);
  pinMode(Config::MOTOR_LEFT_DIR1, OUTPUT);
  pinMode(Config::MOTOR_LEFT_DIR2, OUTPUT);
}

void initializeSensors() {
  pinMode(Config::ULTRASONIC0_TRIG, OUTPUT);
  pinMode(Config::ULTRASONIC0_ECHO, INPUT);
  pinMode(Config::ULTRASONIC1_TRIG, OUTPUT);
  pinMode(Config::ULTRASONIC1_ECHO, INPUT);
  pinMode(Config::BUTTON_PIN, INPUT_PULLUP);
}

void initializeAudio() { pinMode(Config::BUZZER_PIN, OUTPUT); }

void initializeLights() {
  strip1.begin();
  strip2.begin();
  strip1.show();
  strip2.show();
}

// ===============================================
// SENSOR FUNCTIONS
// ===============================================
int readLaserDistance() {
  VL53L0X_RangingMeasurementData_t measurement;
  laserSensor.rangingTest(&measurement, false);
  
  if (measurement.RangeStatus != 4) { // valid measurement
    return measurement.RangeMilliMeter; // distance in mm
  } else {
    return -1; // out of range
  }
}


bool readButtonState() { return digitalRead(Config::BUTTON_PIN) == LOW; }

SensorReadings getAllSensorReadings() {
  SensorReadings r;
  r.laserDistance = readLaserDistance();
  r.ultrasonic0Distance = readUltrasonic(Config::ULTRASONIC0_TRIG, Config::ULTRASONIC0_ECHO);
  r.ultrasonic1Distance = readUltrasonic(Config::ULTRASONIC1_TRIG, Config::ULTRASONIC1_ECHO);
  r.buttonState = readButtonState();
  return r;
}

// ===============================================
// MOTOR FUNCTIONS
// ===============================================
void setMotorSpeeds(int leftSpeed, int rightSpeed) {
  leftSpeed = constrain(leftSpeed, -255, 255);
  rightSpeed = constrain(rightSpeed, -255, 255);

  // Left motor
  if (leftSpeed > 0) {
    digitalWrite(Config::MOTOR_LEFT_DIR1, HIGH);
    digitalWrite(Config::MOTOR_LEFT_DIR2, LOW);
    analogWrite(Config::MOTOR_LEFT_PWM, leftSpeed);
  } else if (leftSpeed < 0) {
    digitalWrite(Config::MOTOR_LEFT_DIR1, LOW);
    digitalWrite(Config::MOTOR_LEFT_DIR2, HIGH);
    analogWrite(Config::MOTOR_LEFT_PWM, -leftSpeed);
  } else {
    digitalWrite(Config::MOTOR_LEFT_DIR1, LOW);
    digitalWrite(Config::MOTOR_LEFT_DIR2, LOW);
    analogWrite(Config::MOTOR_LEFT_PWM, 0);
  }

  // Right motor
  if (rightSpeed > 0) {
    digitalWrite(Config::MOTOR_RIGHT_DIR1, HIGH);
    digitalWrite(Config::MOTOR_RIGHT_DIR2, LOW);
    analogWrite(Config::MOTOR_RIGHT_PWM, rightSpeed);
  } else if (rightSpeed < 0) {
    digitalWrite(Config::MOTOR_RIGHT_DIR1, LOW);
    digitalWrite(Config::MOTOR_RIGHT_DIR2, HIGH);
    analogWrite(Config::MOTOR_RIGHT_PWM, -rightSpeed);
  } else {
    digitalWrite(Config::MOTOR_RIGHT_DIR1, LOW);
    digitalWrite(Config::MOTOR_RIGHT_DIR2, LOW);
    analogWrite(Config::MOTOR_RIGHT_PWM, 0);
  }
}

void executeMotorCommand(MotorDirection dir) {
  int s = robotState.motorSpeed;
  switch (dir) {
    case MotorDirection::FORWARD: setMotorSpeeds(s, s); break;
    case MotorDirection::BACKWARD: setMotorSpeeds(-s, -s); break;
    case MotorDirection::LEFT: setMotorSpeeds(-s, s); break;
    case MotorDirection::RIGHT: setMotorSpeeds(s, -s); break;
    case MotorDirection::STOP: setMotorSpeeds(0, 0); break;
  }
  robotState.currentDirection = dir;
}

// ===============================================
// AUDIO FUNCTIONS
// ===============================================
void playTone(uint16_t freq, uint16_t dur = 0) {
  if (dur > 0) tone(Config::BUZZER_PIN, freq, dur);
  else tone(Config::BUZZER_PIN, freq);
}

void stopTone() { noTone(Config::BUZZER_PIN); }

// ===============================================
// LIGHT FUNCTIONS (non-blocking)
// ===============================================
uint32_t wheelColor(byte pos) {
  pos = 255 - pos;
  if (pos < 85) return strip1.Color(255 - pos * 3, 0, pos * 3);
  else if (pos < 170) { pos -= 85; return strip1.Color(0, pos * 3, 255 - pos * 3); }
  else { pos -= 170; return strip1.Color(pos * 3, 255 - pos * 3, 0); }
}

void setAllPixels(uint32_t color) {
  for (int i = 0; i < Config::NUM_PIXELS; i++) {
    strip1.setPixelColor(i, color);
    strip2.setPixelColor(i, color);
  }
  strip1.show();
  strip2.show();
}

void updateRainbow() {
  for (int i = 0; i < Config::NUM_PIXELS; i++) {
    uint32_t color = wheelColor((i + rainbowIndex) & 255);
    strip1.setPixelColor(i, color);
    strip2.setPixelColor(i, color);
  }
  strip1.show();
  strip2.show();
  rainbowIndex = (rainbowIndex + 1) & 255;
}

// ===============================================
// SERIAL INPUT
// ===============================================
void processSerialCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  if (cmd == "FORWARD") executeMotorCommand(MotorDirection::FORWARD);
  else if (cmd == "BACKWARD") executeMotorCommand(MotorDirection::BACKWARD);
  else if (cmd == "LEFT") executeMotorCommand(MotorDirection::LEFT);
  else if (cmd == "RIGHT") executeMotorCommand(MotorDirection::RIGHT);
  else if (cmd == "STOP") executeMotorCommand(MotorDirection::STOP);
  else if (cmd.startsWith("SPEED:")) robotState.motorSpeed = constrain(cmd.substring(6).toInt(), 0, 255);

 if (cmd == "SCANLEFT") {
    long distance = ScanForObstacles_Left();
    Serial.print("SCANLEFT:"); Serial.println(distance);
  }
  else if (cmd == "SCANRIGHT") {
    long distance = ScanForObstacles_Right();
    Serial.print("SCANRIGHT:"); Serial.println(distance);
  }
}

void handleSerialInput() {
  while (Serial.available()) {
    processSerialCommand(Serial.readStringUntil('\n'));
  }
}

// ===============================================
// BUTTON HANDLING
// ===============================================
void handleButton(bool state) {
  static bool lastState = false;
  static unsigned long lastDebounce = 0;
  const unsigned long debounce = 50;

  if (state != lastState) lastDebounce = millis();

  if ((millis() - lastDebounce) > debounce) {
    if (state != robotState.buttonPressed) {
      robotState.buttonPressed = state;
      if (state) {
        playTone(Config::STARTUP_TONE_FREQ);
        setAllPixels(strip1.Color(255, 0, 0)); // simple indication
      } else {
        stopTone();
        setAllPixels(strip1.Color(0, 0, 0));
      }
    }
  }
  lastState = state;
}

// ===============================================
// MAIN SETUP & LOOP
// ===============================================
void setup() {
  Serial.begin(Config::SERIAL_BAUD_RATE);
  while (!Serial);

  Serial.println(F("=== Robot Startup ==="));
  robotState.systemReady = initializeLaserSensor();
  initializeServo();
  initializeMotors();
  initializeSensors();
  initializeAudio();
  initializeLights();

  // Startup sequence
  playTone(Config::STARTUP_TONE_FREQ, 500);
  delay(500);
  setAllPixels(strip1.Color(255, 255, 255));
  delay(500);
  setAllPixels(strip1.Color(0, 0, 0));
}

void loop() {
  // --- Read sensors ---
  SensorReadings readings = getAllSensorReadings();
  handleButton(readings.buttonState);

  // --- Serial input ---
  handleSerialInput();

  // --- Print sensor status (non-blocking) ---
  if (millis() - lastSensorPrint >= sensorPrintInterval) {
    Serial.print(F("LASER:")); Serial.print(readings.laserDistance);
    Serial.print(" ULTRASONIC0:"); Serial.print(readings.ultrasonic0Distance);
    Serial.print(" ULTRASONIC1:"); Serial.println(readings.ultrasonic1Distance);
    lastSensorPrint = millis();
  }

  // --- Light effects ---
  if (robotState.buttonPressed) {
    if (millis() - lastStrobe >= strobeInterval) {
      static bool on = false;
      setAllPixels(on ? strip1.Color(255, 255, 255) : strip1.Color(0, 0, 0));
      on = !on;
      lastStrobe = millis();
    }
  }

  

  // --- Rainbow animation (always running) ---
  updateRainbow();
}

#include <Servo.h>

// --- LED pins ---
const int led1 = 2; // Front lights
const int led2 = 3; // Back lights

// --- Sensor pins ---
const int metalDetectorPin = A0;   // Metal detector sensor
#define PHOTO_PIN A1               // PhotoResistor
#define UV_PIN A2                  // UV Module
#define BALLSWITCH_PIN A3          // Ball switch sensor
#define MOTION_PIN 4               // Motion Detector Module

// Line follower module pins (3 sensors: left, middle, right)
#define LF_LEFT 8
#define LF_MID  9
#define LF_RIGHT 10

// --- Variables ---
bool motionDetected = false;

// --- Setup ---
void setup() {
  // LEDs
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);

  // Sensors
  pinMode(MOTION_PIN, INPUT);
  pinMode(LF_LEFT, INPUT);
  pinMode(LF_MID, INPUT);
  pinMode(LF_RIGHT, INPUT);
  pinMode(BALLSWITCH_PIN, INPUT);

  // Serial
  Serial.begin(9600);
  Serial.println("=== Multi-Sensor System Ready ===");
}

// --- Main loop ---
void loop() {
  // --- Handle serial commands ---
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "LIGHT_FRONT_ON") {
      TurnOnFrontLights();
      Serial.println("Front lights ON");
    } else if (cmd == "LIGHT_FRONT_OFF") {
      TurnOffFrontLights();
      Serial.println("Front lights OFF");
    } else if (cmd == "LIGHT_BACK_ON") {
      TurnOnBackLights();
      Serial.println("Back lights ON");
    } else if (cmd == "LIGHT_BACK_OFF") {
      TurnOffBackLights();
      Serial.println("Back lights OFF");
    }
  }

  // --- Read sensors ---
  motionDetected = digitalRead(MOTION_PIN);
  int photoValue = analogRead(PHOTO_PIN);
  int uvValue = analogRead(UV_PIN);
  int metalValue = analogRead(metalDetectorPin);
  int ballState = digitalRead(BALLSWITCH_PIN);
  int lfLeft = digitalRead(LF_LEFT);
  int lfMid = digitalRead(LF_MID);
  int lfRight = digitalRead(LF_RIGHT);

  // --- Print all readings in one line ---
  Serial.print("MOTION:"); Serial.print(motionDetected);
  Serial.print(" | PHOTO:"); Serial.print(photoValue);
  Serial.print(" | UV:"); Serial.print(uvValue);
  Serial.print(" | METAL:"); Serial.print(metalValue);
  Serial.print(" | BALL:"); Serial.print(ballState);
  Serial.print(" | LF[L:"); Serial.print(lfLeft);
  Serial.print(" M:"); Serial.print(lfMid);
  Serial.print(" R:"); Serial.print(lfRight);
  Serial.println("]");

if (Serial.available() > 0) {
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "LIGHT_FRONT_ON" || cmd == "TURNONFLIGHTS") {
    TurnOnFrontLights();
    Serial.println("Front lights ON");
  } else if (cmd == "LIGHT_FRONT_OFF") {
    TurnOffFrontLights();
    Serial.println("Front lights OFF");
  } else if (cmd == "LIGHT_BACK_ON") {
    TurnOnBackLights();
    Serial.println("Back lights ON");
  } else if (cmd == "LIGHT_BACK_OFF") {
    TurnOffBackLights();
    Serial.println("Back lights OFF");
  }
}
  // --- Sensor reactions ---
  if (motionDetected) {
    Serial.println("⚠️ Motion detected!");
    TurnOnFrontLights();
  } else {
    TurnOffFrontLights();
  }

  if (metalValue > 350) {
    Serial.println("⚡ METAL DETECTED!");
    BlinkBackLights(2, 150); // flash back lights
  } else {
    TurnOffBackLights();
  }

  if (ballState == HIGH) {
    Serial.println("Ball switch triggered!");
  }

  delay(500); // update rate
}

// --- LED control functions ---
void TurnOnFrontLights() {
  digitalWrite(led1, HIGH);
}

void TurnOffFrontLights() {
  digitalWrite(led1, LOW);
}

void TurnOnBackLights() {
  digitalWrite(led2, HIGH);
}

void TurnOffBackLights() {
  digitalWrite(led2, LOW);
}

void BlinkFrontLights(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    TurnOnFrontLights();
    delay(delayMs);
    TurnOffFrontLights();
    delay(delayMs);
  }
}

void BlinkBackLights(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    TurnOnBackLights();
    delay(delayMs);
    TurnOffBackLights();
    delay(delayMs);
  }
}

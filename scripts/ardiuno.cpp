#include <Servo.h>

// Motor pins
const int IN1 = 17; // Left motor
const int IN2 = 27;
const int ENA = 18; // PWM

const int IN3 = 22; // Right motor
const int IN4 = 23;
const int ENB = 19; // PWM

// Ultrasonic sensor pins (declare BEFORE setup)
const int trigPin = 8;
const int echoPin = 9;

int speedVal = 150; // Base speed (0–255)

Servo scanServo;
int servoPos = 90; // Start center

// Obstacle detection threshold (cm)
const int distanceThreshold = 20;

void setup()
{
    Serial.begin(9600);

    pinMode(IN1, OUTPUT);
    pinMode(IN2, OUTPUT);
    pinMode(ENA, OUTPUT);

    pinMode(IN3, OUTPUT);
    pinMode(IN4, OUTPUT);
    pinMode(ENB, OUTPUT);

    pinMode(trigPin, OUTPUT);
    pinMode(echoPin, INPUT);

    scanServo.attach(10);

    Awake(); // Initial state: Stop
}

const int trigPin = 8;
const int echoPin = 9;

long getDistance()
{
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    long duration = pulseIn(echoPin, HIGH);
    long distance = duration * 0.034 / 2; // cm
    return distance;
}

void loop()
{
    if (Serial.available())
    {
        String command = Serial.readStringUntil('\n');
        command.trim();

        if (command == "FORWARD")
            Forward();
        else if (command == "BACKWARD")
            Backward();
        else if (command == "LEFT")
            Left();
        else if (command == "RIGHT")
            Right();
        else if (command == "STOP")
            Stop();
        else if (command == "AVOID")
            ObstacleAvoidance();
        else if (command == "SPEEDUP")
            SpeedUp();
        else if (command == "SPEEDDOWN")
            SpeedDown();
    }
}

void Awake()
{
    Stop(); // Don't move until commanded
}

void SpeedUp()
{
    speedVal += 25;
    if (speedVal > 255)
        speedVal = 255;
}

void SpeedDown()
{
    speedVal -= 25;
    if (speedVal < 0)
        speedVal = 0;
}

void Forward()
{
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, speedVal);

    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    analogWrite(ENB, speedVal);
}

void Backward()
{
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    analogWrite(ENA, speedVal);

    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    analogWrite(ENB, speedVal);
}

void Left()
{
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
    analogWrite(ENA, speedVal / 2);

    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    analogWrite(ENB, speedVal);
}

void Right()
{
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, speedVal);

    digitalWrite(IN3, LOW);
    digitalWrite(IN4, HIGH);
    analogWrite(ENB, speedVal / 2);
}

void ObstacleAvoidance()
{
    long centerDist = getDistance();

    if (centerDist < distanceThreshold)
    {
        Stop();

        // Scan left
        scanServo.write(45);
        delay(500);
        long leftDist = getDistance();

        // Scan right
        scanServo.write(135);
        delay(500);
        long rightDist = getDistance();

        // Return to center
        scanServo.write(90);
        delay(300);

        if (leftDist > rightDist && leftDist > distanceThreshold)
        {
            Left();
            delay(400);
            Forward();
        }
        else if (rightDist > distanceThreshold)
        {
            Right();
            delay(400);
            Forward();
        }
        else
        {
            Backward();
            delay(300);
            Stop();
        }
    }
    else
    {
        Forward();
    }
}

void Stop()
{
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, 0);

    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    analogWrite(ENB, 0);
}
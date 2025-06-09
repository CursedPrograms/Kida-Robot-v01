import RPi.GPIO as GPIO
import time
import motorcontrol

# ============================================
# 🧰 Wiring assumptions (change GPIOs if needed):
#
# HC-SR04:
#   TRIG: GPIO 5
#   ECHO: GPIO 6
#
# Servo (SG90 or similar):
#   Control pin: GPIO 12
# ============================================

# GPIO Pins
TRIG = 5
ECHO = 6
SERVO_PIN = 12

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Servo setup
servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
servo.start(0)

def set_servo_angle(angle):
    duty = 2 + (angle / 18)
    GPIO.output(SERVO_PIN, True)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.3)
    GPIO.output(SERVO_PIN, False)
    servo.ChangeDutyCycle(0)

def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO) == 0:
        start_time = time.time()
    while GPIO.input(ECHO) == 1:
        stop_time = time.time()

    elapsed = stop_time - start_time
    distance = (elapsed * 34300) / 2
    return distance

def scan():
    scan_result = {}
    for angle in [0, 90, 180]:  # Left, Center, Right
        set_servo_angle(angle)
        dist = get_distance()
        scan_result[angle] = dist
        print(f"📡 Angle {angle}°: {dist:.1f} cm")
    return scan_result

def avoid_obstacle():
    scan_data = scan()
    front = scan_data[90]
    left = scan_data[0]
    right = scan_data[180]

    if front < 25:
        motorcontrol.stop()
        time.sleep(0.2)

        if left > right and left > 30:
            print("🔀 Turning left...")
            motorcontrol.left_fast()
        elif right > left and right > 30:
            print("🔀 Turning right...")
            motorcontrol.right_fast()
        else:
            print("🔄 Reversing...")
            motorcontrol.backward()
        time.sleep(0.7)
        motorcontrol.stop()
    else:
        print("✅ Path clear. Moving forward...")
        motorcontrol.forward()

# === MAIN LOOP ===
if __name__ == "__main__":
    try:
        while True:
            avoid_obstacle()
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("🛑 Shutdown initiated.")
        motorcontrol.stop()
        servo.stop()
        GPIO.cleanup()

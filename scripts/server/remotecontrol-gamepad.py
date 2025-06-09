import pygame
import motorcontrol
import time

# Init pygame for joystick
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("🎮 No gamepad detected. Plug one in and try again.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"🎮 Gamepad connected: {joystick.get_name()}")

def handle_input():
    pygame.event.pump()  # Update joystick state

    axis_y = joystick.get_axis(1)  # Left stick vertical
    axis_x = joystick.get_axis(0)  # Left stick horizontal

    threshold = 0.2  # Deadzone threshold

    # Forward / Backward
    if axis_y < -threshold:
        motorcontrol.forward(100)
    elif axis_y > threshold:
        motorcontrol.backward(100)
    # Turning
    elif axis_x < -threshold:
        motorcontrol.left_slow(100)
    elif axis_x > threshold:
        motorcontrol.right_slow(100)
    else:
        motorcontrol.stop()

try:
    print("🕹️ Use the left joystick to move. Ctrl+C to quit.")
    while True:
        handle_input()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 Stopping...")
    motorcontrol.stop()
    pygame.quit()
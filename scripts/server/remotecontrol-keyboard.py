import pygame
import motorcontrol
import time

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("KIDA Keyboard Control")

print("⌨️ Use W/A/S/D or Arrow Keys to control KIDA. Press ESC or close the window to quit.")

# Track last movement to prevent repeated commands
current_motion = None

def handle_keys(keys):
    global current_motion

    forward_key = keys[pygame.K_w] or keys[pygame.K_UP]
    back_key = keys[pygame.K_s] or keys[pygame.K_DOWN]
    left_key = keys[pygame.K_a] or keys[pygame.K_LEFT]
    right_key = keys[pygame.K_d] or keys[pygame.K_RIGHT]

    if forward_key:
        if current_motion != "forward":
            motorcontrol.forward()
            current_motion = "forward"
    elif back_key:
        if current_motion != "backward":
            motorcontrol.backward()
            current_motion = "backward"
    elif left_key:
        if current_motion != "left":
            motorcontrol.left_slow()
            current_motion = "left"
    elif right_key:
        if current_motion != "right":
            motorcontrol.right_slow()
            current_motion = "right"
    else:
        if current_motion is not None:
            motorcontrol.stop()
            current_motion = None

# Main loop
try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    running = False
                handle_keys(keys)

        time.sleep(0.05)

except KeyboardInterrupt:
    pass

finally:
    print("🛑 Shutting down KIDA control...")
    motorcontrol.stop()
    pygame.quit()

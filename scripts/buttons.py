import pygame
import threading
import state_machine
import ObstacleAvoidance
from leds import toggle_leds
from camera_actions import take_photo, start_video, stop_video, check_recording_timeout
from music import play_next_track, stop_music, skip_music
from arduino import send_command

class Button:
    def __init__(self, rect, color, text, action):
        self.rect = pygame.Rect(rect)
        self.base_color = color
        self.hover_color = (min(color[0]+30,255), min(color[1]+30,255), min(color[2]+30,255))
        self.pressed_color = (max(color[0]-30,0), max(color[1]-30,0), max(color[2]-30,0))
        self.text = text
        self.action = action
        self.font = pygame.font.SysFont(None, 20)
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, surface):
        color = self.base_color
        if self.is_pressed:
            color = self.pressed_color
        elif self.is_hovered:
            color = self.hover_color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, (80,80,80), self.rect, 2, border_radius=12)
        label = self.font.render(self.text, True, (0, 0, 0))
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def update(self, mouse_pos, mouse_down):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.is_pressed = self.is_hovered and mouse_down

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def create_buttons():
    pink = (255, 182, 193)

    def enable_keyboard():
        send_command("dev00", "KEYBOARDCONTROL")
        state_machine.keyboard_control = True
        print("🔑 Keyboard control mode enabled")

    def enable_autonomous():
        send_command("dev00", "SELFCONTROL")
        state_machine.keyboard_control = False
        print("🤖 Autonomous mode enabled")

        # Start obstacle avoidance in a separate thread
        if not hasattr(state_machine, "obstacle_thread") or not state_machine.obstacle_thread.is_alive():
            state_machine.obstacle_thread = threading.Thread(
                target=ObstacleAvoidance.run_obstacle_avoidance,
                daemon=True
            )
            state_machine.obstacle_thread.start()
            print("🟢 Obstacle avoidance thread started")

    return [
        Button((650, 20, 160, 40), pink, "Take Photo", take_photo),
        Button((650, 70, 160, 40), pink, "Record Video", start_video),
        Button((650, 120, 160, 40), pink, "Keyboard Mode", enable_keyboard),
        Button((650, 170, 160, 40), pink, "Autonomous Mode", enable_autonomous),
        Button((650, 220, 160, 40), pink, "Play Music", play_next_track),
        Button((650, 270, 160, 40), pink, "Next Track", skip_music),
        Button((650, 320, 160, 40), pink, "Stop Music", stop_music),
        Button((650, 370, 160, 40), pink, "Toggle LEDs", toggle_leds),
    ]

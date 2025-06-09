import subprocess
import pygame
import threading
import time

def play_audio_loop(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except Exception as e:
        print(f"Audio playback error: {e}")

def stop_audio():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except Exception:
        pass

def install_dependencies():
    audio_thread = threading.Thread(target=play_audio_loop, args=("./audio/music/update.mp3",))
    audio_thread.start()

    try:
        with open('requirements.txt', 'r') as requirements_file:
            requirements = requirements_file.readlines()

        for requirement in requirements:
            requirement = requirement.strip()
            if requirement:
                subprocess.run(['pip', 'install', requirement])

        print("Dependencies installed successfully.")

    except Exception as e:
        print(f"Error installing dependencies: {e}")

    finally:
        stop_audio()

if __name__ == "__main__":
    install_dependencies()
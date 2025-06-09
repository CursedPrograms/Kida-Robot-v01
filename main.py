import os
import subprocess
import json
import time
import pygame
import threading
import platform

# Wait for 3 seconds
time.sleep(3)
waitTime = 5.0

# Initialize pygame mixer
pygame.mixer.init()

# Load and play the startup sound
pygame.mixer.music.load("audio/startup.mp3")
pygame.mixer.music.play()

# Wait until the sound finishes playing
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)

# === Voice Commands Map ===
if platform.system() == "Windows":
    PYTHON_CMD = "python"
else:
    PYTHON_CMD = "python3"

def run_wakeword():
    print("\nNo user input detected.")
    pygame.mixer.music.load("audio/voice-command.mp3")
    pygame.mixer.music.play()
    time.sleep(6)
    script_file_path = os.path.join(current_script_dir, "scripts/server/wakeword.py")
    if os.path.exists(script_file_path):
        try:
            subprocess.run([PYTHON_CMD, script_file_path])
        except Exception as e:
            print(f"Error running wakeword script: {e}")
    else:
        print(f"Wakeword script '{script_file_path}' does not exist.")
    os._exit(0)  # Exit after running wakeword script to prevent continuing loop


def main():
    global current_script_dir
    with open('config.json') as json_file:
        config_data = json.load(json_file)

    app_name = config_data.get('Config', {}).get('AppName', 'default_app')
    print(app_name)

    scripts = {
        "1": {
            "name": "Run 'Client'",
            "description": "Client",
            "file_name": "scripts/server/os-client.py"
        },
        "2": {
            "name": "Run 'Obstacle Avoidance'",
            "description": "Obstacle Avoidance",
            "file_name": "scripts/server/obstacle-avoidance.py"
        },
        "3": {
            "name": "Run 'Remote Control SSH'",
            "description": "Remote Control SSH",
            "file_name": "scripts/server/remotecontrol-ssh.py"
        },
        "4": {
            "name": "Run 'Remote Control Keyboard'",
            "description": "Remote Control Keyboard",
            "file_name": "scripts/server/remotecontrol-keyboard.py"
        },
        "5": {
            "name": "Run 'Remote Control Gamepad'",
            "description": "Remote Control Gamepad",
            "file_name": "scripts/server/remotecontrol-gamepad.py"
        },
        "6": {
            "name": "Run 'Voice Command'",
            "description": "Voice Command",
            "file_name": "scripts/server/voicecommand.py"
        },
        "00": {
            "name": "Run 'Install Dependencies'",
            "description": "Install Dependencies",
            "file_name": "scripts/install_dependencies.py"
        },
    }

    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    while True:
        print("\nAvailable Scripts:")
        for key, script_info in scripts.items():
            print(f"{key}: {script_info['name']} - {script_info['description']}")

        # Start a timer for 45 seconds to run wakeword script automatically
        timer = threading.Timer(waitTime, run_wakeword)
        timer.start()

        try:
            user_choice = input("Enter the number of the script you want to run (or 'q' to quit): ").strip()
            timer.cancel()  # Cancel the timer since user responded
        except Exception:
            timer.cancel()
            print("\nInput interrupted.")
            break

        if user_choice == 'q':
            break

        if user_choice in scripts:
            selected_script = scripts[user_choice]
            script_file_name = selected_script["file_name"]
            script_file_path = os.path.join(current_script_dir, script_file_name)

            if os.path.exists(script_file_path):
                try:
                    pygame.mixer.music.load("audio/confirmed.mp3")
                    pygame.mixer.music.play()                    
                    subprocess.run([PYTHON_CMD, script_file_path])
                except Exception as e:
                    print(f"An error occurred while running the script: {e}")
            else:
                print(f"Script file '{script_file_name}' does not exist.")
        else:
            print("Invalid choice. Please select a valid script number.")

if __name__ == "__main__":
    main()

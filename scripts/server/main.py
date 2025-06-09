import os
import subprocess
import json
import time
import pygame

# Wait for 3 seconds
time.sleep(3)

# Initialize pygame mixer
pygame.mixer.init()

# Load and play the sound
pygame.mixer.music.load("audio/startup.mp3")
pygame.mixer.music.play()

# Wait until the sound finishes playing
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)

def main():
    with open('config.json') as json_file:
        config_data = json.load(json_file)

    # Get the project name from the JSON data
    app_name = config_data.get('Config', {}).get('AppName', 'default_app')

    # Print the actual app name value
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
            "name": "Run 'Remote Control SSH",
            "description": "Remote Control SSH",
            "file_name": "scripts/server/remotecontrol-ssh.py"
        },
        "4": {"name": "Run 'Remote Control Keyboard",
            "description": "Remote Control SSH",
            "file_name": "scripts/server/remotecontrol-keyboard.py"
        },
        "5": {"name": "Run 'Remote Control Gamepad",
            "description": "Remote Control SSH",
            "file_name": "scripts/server/remotecontrol-gamepad.py"
        },
        "6": {"name": "Run 'Voice Command",
            "description": "Remote Control SSH",
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
        
        user_choice = input("Enter the number of the script you want to run (or 'q' to quit): ").strip()
        
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
                    subprocess.run(["python", script_file_path])
                except Exception as e:
                    print(f"An error occurred while running the script: {e}")
            else:
                print(f"Script file '{script_file_name}' does not exist.")
        else:
            print("Invalid choice. Please select a valid script number.")

if __name__ == "__main__":
    main()

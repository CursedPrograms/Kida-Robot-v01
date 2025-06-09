import os
import time
import speech_recognition as sr
import whisper
import subprocess
import platform
import pygame

pygame.mixer.init()

# === Setup Whisper model ===
print("🔊 Loading Whisper model...")
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")
WHISPER_MODEL_DIR = os.path.join(BASE_DIR, "whisper-base")
model = whisper.load_model("base", download_root=WHISPER_MODEL_DIR)
print("✅ Whisper model loaded.")

# === Setup Speech Recognition ===
recognizer = sr.Recognizer()
mic = sr.Microphone()

# === Voice Commands Map ===
if platform.system() == "Windows":
    PYTHON_CMD = "python"
else:
    PYTHON_CMD = "python3"

COMMANDS = {}

# Helper to register multiple aliases
def register_commands(aliases, command_path):
    for alias in aliases:
        COMMANDS[alias] = lambda path=command_path: subprocess.run([PYTHON_CMD, path])

# Register aliases
register_commands(["chat with me", "talk to me", "i want to chat with you"], "scripts/server/llm-tts-openrouter-googletts.py")
register_commands(["voice control"], "scripts/server/remotecontrol-voice.py")
register_commands(["gamepad control", "gamepad"], "scripts/server/remotecontrol-gamepad.py")
register_commands(["ssh control"], "scripts/server/remotecontrol-ssh.py")
register_commands(["obstacle avoidance", "freeroam"], "scripts/server/obstacle-avoidance.py")

# Special case for 'exit'
COMMANDS["exit"] = "exit"

# === Voice Control Loop ===
def listen_and_execute():
    print("🎤 Say a command...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    print("🧠 Recognizing...")
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio.get_wav_data())

    try:
        result = model.transcribe(AUDIO_FILE)
        command = result["text"].lower().strip()
        print(f"🗣️ You said: {command}")
    except Exception as e:
        print(f"❌ Whisper error: {e}")
        return True

    for word, action in COMMANDS.items():
        if word in command:
            if action == "exit":
                print("🛑 Voice control session ended.")
                return False
            else:
                pygame.mixer.music.load("audio/respond.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                print(f"🚗 Executing: {word}")
                action()
                return True

    print("❌ Command not recognized.")
    return True

# === Main Loop ===
if __name__ == "__main__":
    try:
        running = True
        while running:
            running = listen_and_execute()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n💥 Interrupted by user. Stopping...")

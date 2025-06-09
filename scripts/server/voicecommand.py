import os
import time
import speech_recognition as sr
import whisper
import subprocess
import platform

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

COMMANDS = {
    "voice control": lambda: subprocess.run([PYTHON_CMD, "remotecontrol-voice.py"]),
    "gamepad control": lambda: subprocess.run([PYTHON_CMD, "remotecontrol-gamepad.py"]),
    "ssh control": lambda: subprocess.run([PYTHON_CMD, "remotecontrol-ssh.py"]),
    "obstacle avoidance": lambda: subprocess.run([PYTHON_CMD, "obstacle-avoidance.py"]),
    "freeroam": lambda: subprocess.run([PYTHON_CMD, "obstacle-avoidance.py"]),
    "exit": "exit"
}

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

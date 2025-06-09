import os
import time
import motorcontrol
import speech_recognition as sr
import whisper

# === Setup Whisper model ===
print("🔊 Loading Whisper model...")
# Whisper model
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")
WHISPER_MODEL_DIR = os.path.join(BASE_DIR, "whisper-base")
model = whisper.load_model("base", download_root=WHISPER_MODEL_DIR)
print("✅ Whisper model loaded.")

# === Setup Speech Recognition ===
recognizer = sr.Recognizer()
mic = sr.Microphone()

# === Voice Commands Map ===
COMMANDS = {
    "forward": motorcontrol.forward,
    "backward": motorcontrol.backward,
    "back": motorcontrol.backward,
    "stop": motorcontrol.stop,
    "left": motorcontrol.left_slow,
    "right": motorcontrol.right_slow,
    "exit": "exit"
}

# === Voice Control Loop ===
def listen_and_execute():
    print("🎤 Say a command (e.g. forward, backward, stop)...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    print("🧠 Recognizing...")
    with open("input.wav", "wb") as f:
        f.write(audio.get_wav_data())

    result = model.transcribe("input.wav")
    command = result["text"].lower().strip()
    print(f"🗣️ You said: {command}")

    for word, action in COMMANDS.items():
        if word in command:
            if action == "exit":
                print("🛑 Voice control session ended.")
                motorcontrol.stop()
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
        motorcontrol.stop()
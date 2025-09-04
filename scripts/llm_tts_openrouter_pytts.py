import os
import speech_recognition as sr
import requests
import re
import warnings
import time
from faster_whisper import WhisperModel
import pyttsx3

warnings.filterwarnings("ignore")

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")

# Load faster-whisper model (tiny/int8 = fastest)
model = WhisperModel("tiny", device="cpu", compute_type="int8")

def load_key(path):
    with open(path, "r") as f:
        return f.readline().strip()

OPENROUTER_API_KEY = load_key(os.path.join(BASE_DIR, "keys/openrouter-api-key.txt"))

# Initialize pyttsx3 TTS engine
engine = pyttsx3.init()
engine.setProperty("rate", 175)  # speaking speed
engine.setProperty("volume", 1.0)
engine.setProperty("voice", "en+f3")  # try to pick female voice, may vary by platform

def speak(text):
    expression_match = re.search(r"\b(wink|smile|frown|blush)\b", text)
    expression = expression_match.group(1) if expression_match else None
    spoken = re.sub(r"\b(wink|smile|frown|blush)\b", "", text).replace("*", "").strip()

    if expression:
        print("Expression:", expression)
    print("KIDA says:", spoken)

    try:
        engine.say(spoken)
        engine.runAndWait()
        time.sleep(0.5)  # pause to avoid mic picking up speaker output
    except Exception as e:
        print("Voice error:", e)
        print(spoken)

    return expression

def ask_llm(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are KIDA, a flirty, sarcastic AI tank robot girl. Keep your responses clever, short, and spicy."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 120,
        "temperature": 0.95
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, json=data, timeout=30)
        output = response.json()
        print("🔍 LLM raw response:", output)

        if "choices" in output:
            return output["choices"][0]["message"]["content"].strip()
        elif "error" in output:
            return f"KIDA error: {output['error']['message']}"
        return "I got lost in thought. Try again, sugar."
    except Exception as e:
        print("LLM error:", e)
        return "I'm glitching hard, babe. Try again later."

def transcribe(audio_data):
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio_data.get_wav_data())

    if os.path.getsize(AUDIO_FILE) < 1000:
        return "[Silence]"

    segments, info = model.transcribe(AUDIO_FILE, beam_size=1, without_timestamps=True)
    if hasattr(info, "no_speech_prob") and info.no_speech_prob > 0.6:
        return "[Silence]"

    text = " ".join([seg.text for seg in segments]).strip()
    return text

def list_microphones():
    print("Available microphones:")
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{i}: {name}")

def main():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 400
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.5
    recognizer.non_speaking_duration = 0.5

    # Uncomment below to list mics and choose a device index if needed
    # list_microphones()
    # mic_index = int(input("Select mic device index or press Enter for default: ") or -1)

    print("🔋 KIDA online. Awaiting orders, hotshot.")

    while True:
        try:
            with sr.Microphone() as source:  # Add device_index=mic_index if chosen
                recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Listening... take your time.")
                audio = recognizer.listen(source, timeout=None)

            print("🧠 Recognizing...")
            text = transcribe(audio)

            if text == "[Silence]" or text.strip() == "":
                print("⚠️ Silence detected, no input.")
                continue

            print("You said:", text)

            if text.lower() in ["quit", "exit", "shutdown"]:
                speak("Going dark. Goodbye, commander.")
                break

            reply = ask_llm(text)
            speak(reply)

        except Exception as e:
            print("Error:", e)
            speak("Oops. System hiccup. Try again, babe.")

if __name__ == "__main__":
    main()

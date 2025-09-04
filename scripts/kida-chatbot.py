import os
import re
import tempfile
import subprocess
import speech_recognition as sr
import whisper
import requests
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_AUDIODRIVER"] = "alsa"

from elevenlabs import ElevenLabs

import warnings, sys, os

# Suppress Whisper FP16 warning
warnings.filterwarnings("ignore", category=UserWarning)

# Hide ALSA/JACK spam
sys.stderr = open(os.devnull, "w")

# === CONFIG ===

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")
WHISPER_MODEL_DIR = os.path.join(BASE_DIR, "whisper-base")

# Load Whisper model
model = whisper.load_model("base", download_root=WHISPER_MODEL_DIR)

# === LOAD API KEYS FROM FILE ===
def load_key(path):
    with open(path, "r") as f:
        return f.readline().strip()

OPENROUTER_API_KEY = load_key(os.path.join(BASE_DIR, "keys/openrouter-api-key.txt"))
ELEVEN_API_KEY = load_key(os.path.join(BASE_DIR, "keys/elevenlabs-api-key.txt"))

# ElevenLabs client
client = ElevenLabs(api_key=ELEVEN_API_KEY)

# Voice selection
selected_voice = "Rachel"
print("🎙️ Using voice:", selected_voice)


# === VOICE OUTPUT ===
def speak(text):
    expression_match = re.search(r"\b(wink|smile|frown|blush)\b", text)
    expression = expression_match.group(1) if expression_match else None
    spoken = re.sub(r"\b(wink|smile|frown|blush)\b", "", text).replace("*", "").strip()

    if expression:
        print("Expression:", expression)
    print("KIDA says:", spoken)

    try:
        audio = client.generate(
            text=spoken,
            voice=selected_voice,
            model="eleven_monolingual_v1"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio)
            f.flush()
            subprocess.run(["aplay", "-q", f.name])
    except Exception as e:
        print("❌ Voice error:", e)
        print(spoken)

    return expression



# === LLM REQUEST ===
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
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=data, timeout=30
        )
        output = response.json()
        print("🔍 Full LLM response:", output)  # <-- full debug

        if "choices" in output and output["choices"]:
            reply = output["choices"][0]["message"]["content"].strip()
            print("🤖 LLM reply:", reply)        # <-- log reply
            return reply
        elif "error" in output:
            print("❌ LLM Error:", output["error"])
            return f"KIDA error: {output['error']['message']}"
        else:
            print("❌ Unexpected LLM response format")
            return "I got lost in thought. Try again, sugar."
    except Exception as e:
        print("❌ LLM request failed:", e)
        return "I'm glitching hard, babe. Try again later."

# === TRANSCRIPTION ===
def transcribe(audio_data):
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio_data.get_wav_data())

    if os.path.getsize(AUDIO_FILE) < 1000:
        return "[Silence]"

    result = model.transcribe(AUDIO_FILE)
    return result["text"]


# === MAIN LOOP ===
def main():
    recognizer = sr.Recognizer()
    print("🔋 KIDA online. Awaiting orders, hotshot.")

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                print("🎤 Listening...")
                audio = recognizer.listen(source, timeout=10)

                print("🧠 Recognizing...")
                text = transcribe(audio)
                print("You said:", text)

                if text.lower() in ["quit", "exit", "shutdown"]:
                    speak("Going dark. Goodbye, commander.")
                    break

                reply = ask_llm(text)
                speak(reply)

        except sr.WaitTimeoutError:
            print("⏱️ Listening timed out.")
            speak("You gonna say something or just stare at me?")
        except Exception as e:
            print("Error:", e)
            speak("Oops. System hiccup. Try again, babe.")


if __name__ == "__main__":
    main()

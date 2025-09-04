import os
import speech_recognition as sr
import requests
from gtts import gTTS
import re
import tempfile
import pygame
import warnings
import threading
from queue import Queue
from faster_whisper import WhisperModel

warnings.filterwarnings("ignore")

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")

model = WhisperModel("tiny", device="cpu", compute_type="int8")  # tiny/int8 = fastest

def load_key(path):
    with open(path, "r") as f:
        return f.readline().strip()

OPENROUTER_API_KEY = load_key(os.path.join(BASE_DIR, "keys/openrouter-api-key.txt"))

pygame.mixer.init()

# === TASK QUEUE ===
task_queue = Queue()

# === VOICE OUTPUT ===
def speak(text):
    expression_match = re.search(r"\b(wink|smile|frown|blush)\b", text)
    expression = expression_match.group(1) if expression_match else None
    spoken = re.sub(r"\b(wink|smile|frown|blush)\b", "", text).replace("*", "").strip()

    if expression:
        print("Expression:", expression)
    print("KIDA says:", spoken)

    try:
        tts = gTTS(spoken)
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(tmp_path)
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print("Voice error:", e)
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

# === ASYNC TRANSCRIPTION ===
def transcribe_async(audio_data, callback):
    def worker():
        with open(AUDIO_FILE, "wb") as f:
            f.write(audio_data.get_wav_data())

        if os.path.getsize(AUDIO_FILE) < 1000:
            callback("[Silence]")
            return

        segments, info = model.transcribe(AUDIO_FILE, beam_size=1, without_timestamps=True)
        if hasattr(info, "no_speech_prob") and info.no_speech_prob > 0.6:
            callback("[Silence]")
            return

        text = " ".join([seg.text for seg in segments]).strip()
        callback(text)

    threading.Thread(target=worker, daemon=True).start()

# === TASK WORKER ===
def process_tasks():
    while True:
        text = task_queue.get()
        if text.lower() in ["quit", "exit", "shutdown"]:
            speak("Going dark. Goodbye, commander.")
            os._exit(0)
        elif text and text not in ["[Silence]", ""]:
            reply = ask_llm(text)
            speak(reply)
        task_queue.task_done()

threading.Thread(target=process_tasks, daemon=True).start()

# === MAIN LOOP ===
def main():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 400  # tweak for sensitivity
    recognizer.dynamic_energy_threshold = True

    print("🔋 KIDA online. Awaiting orders, hotshot.")

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Waiting for speech...")

                # Wait indefinitely for the user to speak
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)

                print("🧠 Recognizing...")

                def handle_text(text):
                    if text.strip() == "" or text == "[Silence]":
                        print("⚠️ Ignored silence / noise")
                        return
                    print("You said:", text)
                    task_queue.put(text)

                transcribe_async(audio, handle_text)

        except Exception as e:
            print("Error:", e)
            speak("Oops. System hiccup. Try again, babe.")

if __name__ == "__main__":
    main()

import os
import speech_recognition as sr
import whisper
import requests
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import pygame
import threading
import re

# === CONFIG ===

# Whisper model
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")
WHISPER_MODEL_DIR = os.path.join(BASE_DIR, "whisper-base")
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
print("🎙️ Using voice: Rachel")

# === PYGAME DISPLAY ===

pygame.init()
screen = None
current_img = None

image_cache = {}

def update_image(image_path):
    global current_img
    if current_img == image_path:
        return
    try:
        if image_path not in image_cache:
            image_cache[image_path] = pygame.image.load(image_path)
        img = image_cache[image_path]
        screen.blit(img, (0, 0))
        pygame.display.flip()
        current_img = image_path
    except Exception as e:
        print(f"Image load error: {e}")

def run_pygame_loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                os._exit(0)

# Start image window in background thread
threading.Thread(target=run_pygame_loop, daemon=True).start()
def init_display():
    global screen, current_img
    pygame.display.set_caption("KIDA")
    screen = pygame.display.set_mode((341, 512))  # or dynamically set size later
    update_image(os.path.join(BASE_DIR, "images", "idle.png"))

# === VOICE OUTPUT ===
def speak(text):
    # Extract expression keywords like "wink", "smile", etc. (you can expand this list)
    expression_match = re.search(r"\b(wink|smile|frown|blush)\b", text)
    expression = expression_match.group(1) if expression_match else None

    # Remove the expression from spoken text
    spoken = re.sub(r"\b(wink|smile|frown|blush)\b", "", text)
    spoken = spoken.replace("*", "").strip()

    # Debug print
    if expression:
        print("Expression:", expression)
    print("KIDA says:", spoken)

    try:
        audio = client.generate(
            text=spoken,
            voice=selected_voice,
            model="eleven_monolingual_v1"
        )
        play(audio)
    except Exception as e:
        print("Voice error:", e)
        print(spoken)


    finally:
        update_image(os.path.join(BASE_DIR, "images", "idle.png"))

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
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
        output = response.json()
        print("🔍 LLM raw response:", output)

        if "choices" in output:
            return output["choices"][0]["message"]["content"].strip()
        elif "error" in output:
            return f"KIDA error: {output['error']['message']}"
        else:
            return "I got lost in thought. Try again, sugar."
    except Exception as e:
        print("LLM error:", e)
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
                update_image(os.path.join(BASE_DIR, "images", "listen.png"))
                audio = recognizer.listen(source, timeout=10)

                print("🧠 Recognizing...")
                update_image(os.path.join(BASE_DIR, "images", "idle.png"))
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
    init_display()
    main()

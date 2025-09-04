import os
import re
import time
import tempfile
import queue
import threading
import argparse
import sys

import speech_recognition as sr
import whisper
import requests
from gtts import gTTS
import pygame

# --- Hailo imports ---
from hailo_whisper_pipeline import HailoWhisperPipeline
from common.audio_utils import load_audio
from common.preprocessing import preprocess, improve_input_audio
from common.postprocessing import clean_transcription
from whisper_hef_registry import HEF_REGISTRY

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")
WHISPER_MODEL_DIR = os.path.join(BASE_DIR, "whisper-base")
OPENROUTER_API_KEY_PATH = os.path.join(BASE_DIR, "keys/openrouter-api-key.txt")

# Thread-safe queue for UI messages
ui_messages = queue.Queue()

def log_to_ui(message):
    try:
        ui_messages.put_nowait(message)
    except queue.Full:
        pass

def load_key(path):
    with open(path, "r") as f:
        return f.readline().strip()

OPENROUTER_API_KEY = load_key(OPENROUTER_API_KEY_PATH)

# === ARGUMENT PARSER ===
def get_args():
    parser = argparse.ArgumentParser(description="Whisper Hailo Pipeline")
    parser.add_argument(
        "--reuse-audio",
        action="store_true",
        help="Reuse the previous audio file (sampled_audio.wav)"
    )
    parser.add_argument(
        "--hw-arch",
        type=str,
        default="hailo8",
        choices=["hailo8", "hailo8l"],
        help="Hardware architecture to use (default: hailo8)"
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="base",
        choices=["base", "tiny"],
        help="Whisper variant to use (default: base)"
    )
    parser.add_argument(
        "--multi-process-service",
        action="store_true",
        help="Enable multi-process service to run other models in addition to Whisper"
    )
    return parser.parse_args()

args = get_args()

USE_HAILO = True  # Set False to fallback to standard Whisper
VARIANT = args.variant
HW_ARCH = args.hw_arch

if USE_HAILO:
    try:
        ENCODER_HEF_PATH = HEF_REGISTRY[VARIANT][HW_ARCH]["encoder"]
        DECODER_HEF_PATH = HEF_REGISTRY[VARIANT][HW_ARCH]["decoder"]

        if not os.path.exists(ENCODER_HEF_PATH) or not os.path.exists(DECODER_HEF_PATH):
            raise FileNotFoundError("One or both Hailo HEF files not found. "
                                    "Please run download_resources.sh or place the HEF files accordingly.")

        hailo_whisper = HailoWhisperPipeline(ENCODER_HEF_PATH, DECODER_HEF_PATH, VARIANT)
    except KeyError:
        raise ValueError(f"No HEF paths found for variant '{VARIANT}' and arch '{HW_ARCH}' in HEF_REGISTRY.")
else:
    model = whisper.load_model("base", download_root=WHISPER_MODEL_DIR)

# === VOICE OUTPUT ===
pygame.mixer.init()

def speak(text):
    expression_match = re.search(r"\b(wink|smile|frown|blush)\b", text)
    expression = expression_match.group(1) if expression_match else None
    spoken = re.sub(r"\b(wink|smile|frown|blush)\b", "", text).replace("*", "").strip()

    if expression:
        print("Expression:", expression)
        log_to_ui(f"Expression: {expression}")

    print("KIDA says:", spoken)
    log_to_ui(f"KIDA says: {spoken}")

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
        log_to_ui(f"Voice error: {e}")
        print(spoken)
        log_to_ui(spoken)
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
        log_to_ui("🔍 LLM raw response received")
        if "choices" in output:
            return output["choices"][0]["message"]["content"].strip()
        elif "error" in output:
            return f"KIDA error: {output['error']['message']}"
        else:
            return "I got lost in thought. Try again, sugar."
    except Exception as e:
        print("LLM error:", e)
        log_to_ui(f"LLM error: {e}")
        return "I'm glitching hard, babe. Try again later."

# === TRANSCRIPTION ===
def transcribe(audio_data):
    """
    Use Hailo Whisper if enabled, else fallback to OpenAI Whisper.
    """
    with open(AUDIO_FILE, "wb") as f:
        f.write(audio_data.get_wav_data())

    if os.path.getsize(AUDIO_FILE) < 1000:
        return "[Silence]"

    if USE_HAILO:
        sampled_audio = load_audio(AUDIO_FILE)
        sampled_audio, start_time = improve_input_audio(sampled_audio, vad=True)
        chunk_offset = max(0, start_time - 0.2)
        chunk_length = 10 if VARIANT == "tiny" else 5

        mel_spectrograms = preprocess(
            sampled_audio,
            is_nhwc=True,
            chunk_length=chunk_length,
            chunk_offset=chunk_offset
        )

        full_transcription = ""
        for mel in mel_spectrograms:
            hailo_whisper.send_data(mel)
            time.sleep(0.2)  # Give time to process
            raw_transcription = hailo_whisper.get_transcription()
            clean_text = clean_transcription(raw_transcription)
            full_transcription += clean_text + " "
        return full_transcription.strip()
    else:
        result = model.transcribe(AUDIO_FILE)
        return result["text"]

# === MAIN LOOP ===
def main():
    recognizer = sr.Recognizer()
    print("🔋 KIDA online. Awaiting orders, hotshot.")
    log_to_ui("🔋 KIDA online. Awaiting orders, hotshot.")

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                print("🎤 Listening...")
                log_to_ui("🎤 Listening...")
                audio = recognizer.listen(source, timeout=10)
                print("🧠 Recognizing...")
                log_to_ui("🧠 Recognizing...")
                text = transcribe(audio)
                print("You said:", text)
                log_to_ui(f"You said: {text}")

                if text.lower() in ["quit", "exit", "shutdown"]:
                    speak("Going dark. Goodbye, commander.")
                    break

                reply = ask_llm(text)
                speak(reply)

        except sr.WaitTimeoutError:
            print("⏱️ Listening timed out.")
            log_to_ui("⏱️ Listening timed out.")
            speak("You gonna say something or just stare at me?")

        except Exception as e:
            print("Error:", e)
            log_to_ui(f"Error: {e}")
            speak("Oops. System hiccup. Try again, babe.")

if __name__ == "__main__":
    main()

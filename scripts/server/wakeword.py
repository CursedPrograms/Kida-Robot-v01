import whisper
import sounddevice as sd
import numpy as np
import time
import os
import pygame
import sys

pygame.mixer.init()

DURATION = 3  # seconds
SAMPLE_RATE = 16000
THRESHOLD_PHRASE = "hello"

# Whisper model
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
AUDIO_FILE = os.path.join(BASE_DIR, "input.wav")
WHISPER_MODEL_DIR = os.path.join(BASE_DIR, "whisper-base")
model = whisper.load_model("tiny", download_root=WHISPER_MODEL_DIR)

def record_audio(duration=DURATION, fs=SAMPLE_RATE):
    print("🎙️ Listening...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()
    audio = np.squeeze(audio)
    return (audio * 32767).astype(np.int16)

def save_wav(audio, filename, fs=SAMPLE_RATE):
    from scipy.io.wavfile import write
    write(filename, fs, audio)

def listen_for_wakeword():
    while True:
        audio = record_audio()
        save_wav(audio, "chunk.wav")

        try:
            result = model.transcribe("chunk.wav", fp16=False)
            text = result["text"].lower().strip()
            print(f"🧠 Heard: {text}")

            if THRESHOLD_PHRASE in text:
                print("🚨 Wake word detected!")
                pygame.mixer.music.load("audio/respond.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                # Determine correct Python command based on OS
                python_cmd = "python3" if sys.platform != "win32" else "python"
                os.system(f"{python_cmd} scripts/server/voicecommand.py")
                break

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(0.5)

if __name__ == "__main__":
    listen_for_wakeword()

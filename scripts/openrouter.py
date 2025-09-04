import requests
import pygame
import sounddevice as sd
import numpy as np
import io
import wave
from pydub import AudioSegment
import pyttsx3


OPENROUTER_API_KEY = "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"

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def record_audio(duration=5, fs=16000):
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    print("Done recording")

    with io.BytesIO() as wav_io:
        wav_file = wave.open(wav_io, 'wb')
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(fs)
        wav_file.writeframes(recording.tobytes())
        wav_file.close()
        wav_data = wav_io.getvalue()

    return wav_data

def speech_to_text(audio_data):
    url = "https://openrouter.ai/api/stt"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "audio/wav"
    }
    response = requests.post(url, headers=headers, data=audio_data)
    text = response.json().get("text", "")
    return text

if __name__ == "__main__":
    text_to_speech("Hello, I am KIDA. How can I assist you today?")
    audio = record_audio(duration=4)
    user_text = speech_to_text(audio)
    print("You said:", user_text)

    if "move" in user_text.lower():
        text_to_speech("Okay, moving forward now.")

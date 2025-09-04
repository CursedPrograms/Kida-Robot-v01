import pygame
import os
import config
import leds  # new import

playlist = []
current_track = -1

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def init_music():
    pygame.mixer.init()
    load_playlist()
    pygame.mixer.music.set_endevent(pygame.USEREVENT)

def load_playlist():
    global playlist
    playlist = [
        os.path.join(config.MUSIC_FOLDER, f)
        for f in os.listdir(config.MUSIC_FOLDER)
        if f.lower().endswith(config.SUPPORTED_FORMATS)
    ]
    playlist.sort()

def play_next_track():
    global current_track
    if not playlist:
        print("⚠️ No tracks found")
        return
    track = playlist[current_track]
    pygame.mixer.music.load(track)
    pygame.mixer.music.play()
    leds.start_music_wave()
    print(f"▶️ Playing: {track}")
    current_track = (current_track + 1) % len(playlist)  # ✅ increment here


def stop_music():
    pygame.mixer.music.stop()
    leds.stop_music_wave()  # stop LEDs
    print("⏹️ Music stopped")

def skip_music():
    stop_music()
    play_next_track()

def is_music_playing():
    return pygame.mixer.music.get_busy()

def handle_music_event(event):
    if event.type == pygame.USEREVENT:
        if not is_music_playing():
            play_next_track()

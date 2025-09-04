from gpiozero import PWMLED
import time
import math
import random
import threading

LED_PINS = [17, 27]
leds = [PWMLED(pin) for pin in LED_PINS]

led_on = False
effect_on = False
effect_thread = None
stop_effect = False

def setup_leds():
    for led in leds:
        led.off()

def startup_led_fade():
    """Smooth fade effect once at startup."""
    duration = 4
    fade_time = 0.02
    steps = int(duration / fade_time)

    for i in range(steps):
        for idx, led in enumerate(leds):
            brightness = (0.5 + 0.5 * math.sin(2 * math.pi * (i / steps) + idx))
            led.value = brightness  # value from 0.0 to 1.0
        time.sleep(fade_time)

    for led in leds:
        led.off()

import threading

def run_chase_effect(duration=15):
    global stop_effect, effect_on, effect_thread

    if effect_on:
        stop_effect = True
        if effect_thread:
            effect_thread.join()
        effect_on = False

    stop_effect = False
    effect_on = True

    # Run chase effect in this thread (blocking)
    _chase_effect_thread = threading.Thread(target=_chase_effect)
    _chase_effect_thread.start()

    # Wait for duration
    time.sleep(duration)

    # Signal effect to stop and wait for effect thread to finish
    stop_effect = True
    _chase_effect_thread.join()

    # Turn off LEDs
    for led in leds:
        led.off()

    effect_on = False
    print("✅ Celebration LEDs off")

def _fade_effect():
    global stop_effect
    while not stop_effect:
        for i in range(101):
            if stop_effect: break
            for led in leds:
                led.value = i / 100
            time.sleep(0.01)
        for i in range(100, -1, -1):
            if stop_effect: break
            for led in leds:
                led.value = i / 100
            time.sleep(0.01)
    for led in leds:
        led.off()

def _strobe_effect():
    global stop_effect
    while not stop_effect:
        for led in leds:
            led.on()
        time.sleep(0.1)
        for led in leds:
            led.off()
        time.sleep(0.1)

def _chase_effect():
    global stop_effect
    while not stop_effect:
        for led in leds:
            led.on()
            time.sleep(0.1)
            led.off()

def _wave_effect():
    global stop_effect
    steps = 100
    while not stop_effect:
        for i in range(steps):
            if stop_effect:
                break
            for idx, led in enumerate(leds):
                brightness = (0.5 + 0.5 * math.sin(2 * math.pi * (i / steps) + idx))
                led.value = brightness
            time.sleep(0.02)
    for led in leds:
        led.off()

def _random_flash_effect():
    global stop_effect
    while not stop_effect:
        led = random.choice(leds)
        led.on()
        time.sleep(0.05)
        led.off()
        time.sleep(0.05)

def toggle_leds():
    global led_on, stop_effect, effect_on, effect_thread
    if effect_on:
        stop_effect = True
        if effect_thread:
            effect_thread.join()
        effect_on = False

    led_on = not led_on
    if led_on:
        for led in leds:
            led.on()
    else:
        for led in leds:
            led.off()
    print("💡 LEDs Solid", "ON" if led_on else "OFF")

def toggle_effects():
    global effect_on, stop_effect, effect_thread, led_on
    if effect_on:
        stop_effect = True
        if effect_thread:
            effect_thread.join()
        effect_on = False
        for led in leds:
            led.off()
        print("✨ LED effects OFF")
    else:
        stop_effect = False
        led_on = False
        effect = random.choice([_fade_effect, _strobe_effect, _chase_effect, _wave_effect, _random_flash_effect])
        effect_thread = threading.Thread(target=effect, daemon=True)
        effect_thread.start()
        effect_on = True
        print(f"✨ LED effects ON → {effect.__name__}")

def start_music_wave():
    global effect_thread, stop_effect, effect_on
    if effect_on:
        stop_effect = True
        if effect_thread:
            effect_thread.join()
        effect_on = False
    stop_effect = False
    effect_thread = threading.Thread(target=_wave_effect, daemon=True)
    effect_thread.start()
    print("🎵 LED wave effect started")

def stop_music_wave():
    global stop_effect, effect_thread
    stop_effect = True
    if effect_thread:
        effect_thread.join()
        effect_thread = None
    for led in leds:
        led.off()
    print("🎵 LED wave effect stopped")

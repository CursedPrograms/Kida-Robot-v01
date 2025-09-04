# camera_actions.py
import os
import time
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
import config

# Directories
IMAGE_DIR = config.IMAGE_DIR
VIDEO_DIR = config.VIDEO_DIR

# Ensure directories exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# Camera globals
picam2 = None
recording = False
record_start_time = None
video_filename = None
encoder = None  # keep a reference

# ----------------------------
# Camera setup
# ----------------------------
def set_camera(cam=None):
    """Initialize the global camera reference."""
    global picam2
    if cam is None:
        picam2 = Picamera2()
        preview_config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        picam2.configure(preview_config)
        picam2.start()
    else:
        picam2 = cam
    print("✅ Camera initialized.")

def take_photo():
    """Capture a photo and save it to IMAGE_DIR."""
    global picam2, recording
    if recording:
        print("⚠️ Cannot take photo while recording video.")
        return
    if picam2 is None:
        print("❌ Camera not initialized. Call set_camera(cam) first.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(IMAGE_DIR, f"image_{timestamp}.jpg")
    try:
        picam2.capture_file(filename)
        print(f"📸 Image saved: {filename}")
    except Exception as e:
        print(f"❌ Failed to take photo: {e}")

# ----------------------------
# Video recording
# ----------------------------
def start_video():
    """Start recording a video if not already recording."""
    global recording, record_start_time, video_filename, encoder

    if recording:
        print("⚠️ Already recording video!")
        return
    if picam2 is None:
        print("❌ Camera not initialized. Call set_camera(cam) first.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = os.path.join(VIDEO_DIR, f"video_{timestamp}.h264")
    encoder = H264Encoder()

    try:
        picam2.start_recording(encoder, FileOutput(video_filename))
        record_start_time = time.time()
        recording = True
        print(f"🎥 Recording video: {video_filename}")
    except Exception as e:
        print(f"❌ Failed to start recording: {e}")
        encoder = None

def stop_video():
    """Stop video recording if currently recording."""
    global recording, encoder

    if not recording:
        print("⚠️ Not currently recording.")
        return
    if picam2 is None:
        print("❌ Camera not initialized. Call set_camera(cam) first.")
        return

    try:
        picam2.stop_recording()
        print(f"✅ Video recording stopped: {video_filename}")
    except Exception as e:
        print(f"❌ Failed to stop recording: {e}")
    finally:
        recording = False
        encoder = None

# ----------------------------
# Automatic recording timeout
# ----------------------------
def check_recording_timeout(timeout=5):
    """Auto-stop recording after `timeout` seconds."""
    global recording, record_start_time
    if recording and (time.time() - record_start_time) >= timeout:
        stop_video()
        print(f"⏱ Auto-stopped video recording after {timeout} seconds.")

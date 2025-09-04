from picamera2 import Picamera2, Preview
from libcamera import Transform

picam2 = None

import os
from datetime import datetime

# Create unique session folder
SESSION_DIR = os.path.join(
    os.path.expanduser("~/captures"),  # or wherever you want
    datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
)
os.makedirs(SESSION_DIR, exist_ok=True)

IMAGE_DIR = os.path.join(SESSION_DIR, "images")
VIDEO_DIR = os.path.join(SESSION_DIR, "videos")
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)


def setup_camera():
    global picam2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(transform=Transform(rotation=0))
    picam2.configure(config)
    picam2.start_preview(Preview.QTGL)
    picam2.start()
    print("📷 Camera started.")

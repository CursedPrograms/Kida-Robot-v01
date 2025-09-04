from deepface import DeepFace
from PIL import Image, ImageDraw, ImageFont
import os
import json
from picamera2 import Picamera2
import cv2
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def capture_image(picamera, save_path):
    """Capture an image using PiCamera2 and save it."""
    picamera.start()
    time.sleep(2)  # Warm-up camera
    frame = picamera.capture_array()
    picamera.stop()

    # Convert from OpenCV BGR to RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Save with Pillow
    img = Image.fromarray(frame)
    img.save(save_path, "JPEG")
    return save_path

def analyze_face(input_image_path, output_directory, reference_image_path=None):
    try:
        input_img = Image.open(input_image_path)

        # DeepFace analysis
        result = DeepFace.analyze(
            img_path=input_image_path,
            actions=['age', 'gender', 'emotion', 'race'],
            enforce_detection=False
        )

        gender_stats = result[0]['gender']
        age = int(result[0]['age'])
        emotion_stats = result[0]['emotion']
        race_stats = result[0]['race']

        gender = max(gender_stats, key=gender_stats.get)
        emotion = max(emotion_stats, key=emotion_stats.get)
        race = max(race_stats, key=race_stats.get)

        print(f"\nAnalyzed {os.path.basename(input_image_path)}:")
        print("Gender:", gender_stats)
        print("Age:", age)
        print("Emotion:", emotion_stats)
        print("Race:", race_stats)

        identity_match = None
        if reference_image_path:
            try:
                verification = DeepFace.verify(
                    img1_path=reference_image_path,
                    img2_path=input_image_path,
                    enforce_detection=False
                )
                identity_match = verification['verified']
                print(f"Identity Match with {os.path.basename(reference_image_path)}:", identity_match)
            except Exception as e:
                print(f"Identity comparison failed: {e}")

        draw = ImageDraw.Draw(input_img)
        font = ImageFont.load_default()
        draw.text((10, 10), f"Gender: {gender}", font=font, fill=(255, 255, 255))
        draw.text((10, 30), f"Age: {age} yrs", font=font, fill=(255, 255, 255))
        draw.text((10, 50), f"Emotion: {emotion}", font=font, fill=(255, 255, 255))
        draw.text((10, 70), f"Race: {race}", font=font, fill=(255, 255, 255))
        if identity_match is not None:
            draw.text((10, 90), f"Identity Match: {identity_match}", font=font, fill=(255, 255, 255))

        os.makedirs(output_directory, exist_ok=True)
        output_filename = f"{gender.lower()}_age_{age}_emo_{emotion}.jpg"
        output_path = os.path.join(output_directory, output_filename)
        input_img.save(output_path, format='JPEG')

        print("Saved analyzed image:", output_path)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.abspath(__file__))

    with open("settings.json", "r") as file:
        settings = json.load(file)

    input_directory = os.path.join(script_directory, settings["directories"]["input"])
    output_directory = os.path.join(script_directory, settings["directories"]["output"])
    reference_image_path = settings.get("reference_image", None)
    if reference_image_path:
        reference_image_path = os.path.join(script_directory, reference_image_path)

    os.makedirs(input_directory, exist_ok=True)

    # Initialize PiCamera2
    picam2 = Picamera2()
    captured_path = os.path.join(input_directory, "capture.jpg")

    # Capture a new image
    print("Capturing image from PiCamera...")
    capture_image(picam2, captured_path)

    # Analyze captured image
    analyze_face(captured_path, output_directory, reference_image_path)

    print("Face analysis complete.")

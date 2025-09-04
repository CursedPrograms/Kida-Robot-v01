import cv2
import numpy as np
import pygame
from collections import defaultdict
from picamera2 import Picamera2

def inference(
    screen,
    model,
    mode,
    task,
    tracker_path=None,
    count=False,
    show_tracks=False,
):
    if mode == "cam":
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        picam2.configure(config)
        picam2.start()
    else:
        raise ValueError("Only 'cam' mode supported for Pygame preview right now")

    track_history = defaultdict(lambda: [])
    seen_ids_per_class = defaultdict(set)
    clock = pygame.time.Clock()

    while True:
        frame = picam2.capture_array()
        if frame is None:
            continue

        # Run YOLO
        if task == "track":
            results = model.track(frame, conf=0.3, persist=True, tracker=tracker_path)
        elif task == "detect":
            results = model.predict(frame, conf=0.5)
        else:
            raise ValueError("Invalid task. Use 'detect' or 'track'.")

        annotated_frame = results[0].plot()

        # FPS calc
        fps = clock.get_fps()
        cv2.putText(
            annotated_frame, f"FPS: {fps:.2f}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )

        # Convert BGR → RGB for Pygame, and flip horizontally if needed
        annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        annotated_frame = cv2.flip(annotated_frame, 1)

        # Create Pygame surface
        frame_surface = pygame.surfarray.make_surface(annotated_frame.swapaxes(0, 1))

        # Draw camera feed in a smaller overlay (top-right corner)
        camera_rect = pygame.Rect(500, 20, 280, 210)
        frame_surface = pygame.transform.scale(
            frame_surface, (camera_rect.width, camera_rect.height)
        )
        screen.blit(frame_surface, camera_rect.topleft)

        # Update only the camera rectangle (prevents UI wipe)
        pygame.display.update(camera_rect)

        clock.tick(30)  # Limit FPS

        # Check for quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                picam2.stop()
                return

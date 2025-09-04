import os
import time
import numpy as np
import cv2
from ultralytics import YOLO
from collections import defaultdict
from picamera2 import Picamera2

# Get the folder where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def download_model_if_missing(model_path):
    if not os.path.isfile(model_path):
        print(f"Model weights '{model_path}' not found. Downloading...")
        YOLO(model_path)  # auto-download
        print("Download complete.")

def inference(
    model,
    mode,
    task,
    tracker_path=None,
    video_path=None,
    save_output=False,
    output_path="output.mp4",
    show_output=True,
    count=False,
    show_tracks=False,
):
    if mode == "cam":
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
        picam2.configure(config)
        picam2.start()
    elif mode == "video":
        if video_path is None:
            raise ValueError("Please provide a valid video path for video mode.")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file {video_path}")
    else:
        raise ValueError("Invalid mode. Use 'cam' or 'video'.")

    track_history = defaultdict(lambda: [])
    seen_ids_per_class = defaultdict(set)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = None

    while True:
        if mode == "cam":
            frame = picam2.capture_array()
            success = frame is not None
        else:
            success, frame = cap.read()

        print(f"Frame read success: {success}, frame shape: {None if frame is None else frame.shape}")
        if not success or frame is None:
            print("Failed to read frame or end of video")
            break

        start_time = time.time()
        class_counts = defaultdict(int)

        if task == "track":
            if tracker_path is None:
                raise ValueError("tracker_path must be provided for tracking task")
            results = model.track(frame, conf=0.3, persist=True, tracker=tracker_path)
        elif task == "detect":
            results = model.predict(frame, conf=0.5)
        else:
            raise ValueError("Invalid task. Use 'detect' or 'track'.")

        end_time = time.time()
        annotated_frame = results[0].plot()

        if results[0].boxes and results[0].boxes.cls is not None:
            boxes = results[0].boxes.xywh.cpu()
            class_ids = results[0].boxes.cls.int().cpu().tolist()
            names = results[0].names

            if task == "track" and results[0].boxes.id is not None:
                track_ids = results[0].boxes.id.int().cpu().tolist()

                for box, cls_id, track_id in zip(boxes, class_ids, track_ids):
                    x, y, w, h = box
                    class_name = names[cls_id]

                    if count:
                        seen_ids_per_class[class_name].add(track_id)

                    if show_tracks:
                        track = track_history[track_id]
                        track.append((float(x), float(y)))
                        if len(track) > 30:
                            track.pop(0)
                        points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                        cv2.polylines(annotated_frame, [points], isClosed=False, color=(230, 230, 230), thickness=10)

            elif task == "detect" and count:
                for cls_id in class_ids:
                    class_counts[names[cls_id]] += 1

        if count:
            x0, y0 = 10, annotated_frame.shape[0] - 80
            if task == "track":
                for i, (cls_name, ids) in enumerate(seen_ids_per_class.items()):
                    label = f"{cls_name}: {len(ids)}"
                    y = y0 + i * 25
                    cv2.putText(annotated_frame, label, (x0, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            elif task == "detect":
                for i, (cls_name, total) in enumerate(class_counts.items()):
                    label = f"{cls_name}: {total}"
                    y = y0 + i * 25
                    cv2.putText(annotated_frame, label, (x0, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        fps = 1 / (end_time - start_time)
        cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if save_output:
            if out is None:
                height, width = annotated_frame.shape[:2]
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            out.write(annotated_frame)

        if show_output:
            cv2.imshow("Raspberry Pi x YOLO11 Inference", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Exiting on user request.")
                break

    if mode == "cam":
        picam2.stop()
    else:
        cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    model_path = os.path.join(SCRIPT_DIR, "yolo11n.pt")
    tracker_path = os.path.join(SCRIPT_DIR, "trackers", "bytetrack.yaml")

    download_model_if_missing(model_path)
    model = YOLO(model_path)

    inference(
        model,
        mode="cam",          # or "video"
        task="track",        # or "detect"
        tracker_path=tracker_path,
        save_output=True,
        show_output=True,
        count=True,
        show_tracks=False,
    )

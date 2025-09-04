import cv2
import time

def camera_loop(picam2, model, task, frame_queue):
    """
    Continuously captures frames from picam2, runs inference if model/task provided,
    and puts annotated frames into frame_queue.
    """
    while True:
        try:
            frame = picam2.capture_array()
            if frame is None:
                continue

            if model and task == "detect":
                results = model.predict(frame, conf=0.5)
                annotated_frame = results[0].plot()
            else:
                annotated_frame = frame

            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            annotated_frame = cv2.flip(annotated_frame, 1)

            if not frame_queue.empty():
                frame_queue.get_nowait()
            frame_queue.put(annotated_frame)

        except Exception as e:
            print(f"Camera loop error: {e}")
            time.sleep(0.1)

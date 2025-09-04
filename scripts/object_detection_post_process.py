#!/usr/bin/env python3
import argparse
import os
import sys
from loguru import logger
import queue
import threading
from functools import partial
from types import SimpleNamespace
import time
from pathlib import Path
import numpy as np
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.tracker.byte_tracker import BYTETracker
from common.hailo_inference import HailoAsyncInference
from common.toolbox import init_input_source, get_labels, load_json_file, preprocess, visualize, id_to_color

# Your provided inference_result_handler and helpers here:
def inference_result_handler(original_frame, infer_results, labels, config_data, tracker=None):
    detections = extract_detections(original_frame, infer_results, config_data)
    frame_with_detections = draw_detections(detections, original_frame, labels, tracker=tracker)
    return frame_with_detections

def draw_detection(image: np.ndarray, box: list, labels: list, score: float, color: tuple, track=False):
    ymin, xmin, ymax, xmax = map(int, box)
    cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
    font = cv2.FONT_HERSHEY_SIMPLEX

    top_text = f"{labels[0]}: {score:.1f}%" if not track or len(labels) == 2 else f"{score:.1f}%"
    bottom_text = None

    if track:
        if len(labels) == 2:
            bottom_text = labels[1]
        else:
            bottom_text = labels[0]

    text_color = (255, 255, 255)
    border_color = (0, 0, 0)

    cv2.putText(image, top_text, (xmin + 4, ymin + 20), font, 0.5, border_color, 2, cv2.LINE_AA)
    cv2.putText(image, top_text, (xmin + 4, ymin + 20), font, 0.5, text_color, 1, cv2.LINE_AA)

    if bottom_text:
        pos = (xmax - 50, ymax - 6)
        cv2.putText(image, bottom_text, pos, font, 0.5, border_color, 2, cv2.LINE_AA)
        cv2.putText(image, bottom_text, pos, font, 0.5, text_color, 1, cv2.LINE_AA)

def denormalize_and_rm_pad(box: list, size: int, padding_length: int, input_height: int, input_width: int) -> list:
    for i, x in enumerate(box):
        box[i] = int(x * size)
        if (input_width != size) and (i % 2 != 0):
            box[i] -= padding_length
        if (input_height != size) and (i % 2 == 0):
            box[i] -= padding_length
    return box

def extract_detections(image: np.ndarray, detections: list, config_data) -> dict:
    visualization_params = config_data["visualization_params"]
    score_threshold = visualization_params.get("score_thres", 0.5)
    max_boxes = visualization_params.get("max_boxes_to_draw", 50)

    img_height, img_width = image.shape[:2]
    size = max(img_height, img_width)
    padding_length = int(abs(img_height - img_width) / 2)

    all_detections = []

    for class_id, detection in enumerate(detections):
        for det in detection:
            bbox, score = det[:4], det[4]
            if score >= score_threshold:
                denorm_bbox = denormalize_and_rm_pad(bbox, size, padding_length, img_height, img_width)
                all_detections.append((score, class_id, denorm_bbox))

    all_detections.sort(reverse=True, key=lambda x: x[0])
    top_detections = all_detections[:max_boxes]

    if not top_detections:
        return {'detection_boxes': [], 'detection_classes': [], 'detection_scores': [], 'num_detections': 0}

    scores, class_ids, boxes = zip(*top_detections)

    return {
        'detection_boxes': list(boxes),
        'detection_classes': list(class_ids),
        'detection_scores': list(scores),
        'num_detections': len(top_detections)
    }

def draw_detections(detections: dict, img_out: np.ndarray, labels, tracker=None):
    boxes = detections["detection_boxes"]
    scores = detections["detection_scores"]
    num_detections = detections["num_detections"]
    classes = detections["detection_classes"]

    if tracker:
        dets_for_tracker = []
        for idx in range(num_detections):
            box = boxes[idx]
            score = scores[idx]
            dets_for_tracker.append([*box, score])
        if not dets_for_tracker:
            return img_out

        online_targets = tracker.update(np.array(dets_for_tracker))
        for track in online_targets:
            track_id = track.track_id
            x1, y1, x2, y2 = track.tlbr
            xmin, ymin, xmax, ymax = map(int, [x1, y1, x2, y2])
            best_idx = find_best_matching_detection_index(track.tlbr, boxes)
            color = tuple(id_to_color(classes[best_idx]).tolist()) if best_idx is not None else (0, 255, 0)
            if best_idx is None:
                draw_detection(img_out, [xmin, ymin, xmax, ymax], [f"ID {track_id}"], track.score * 100.0, color, track=True)
            else:
                draw_detection(img_out, [xmin, ymin, xmax, ymax], [labels[classes[best_idx]], f"ID {track_id}"], track.score * 100.0, color, track=True)
    else:
        for idx in range(num_detections):
            color = tuple(id_to_color(classes[idx]).tolist())
            draw_detection(img_out, boxes[idx], [labels[classes[idx]]], scores[idx] * 100.0, color)

    return img_out

def find_best_matching_detection_index(track_box, detection_boxes):
    best_iou = 0
    best_idx = -1
    for i, det_box in enumerate(detection_boxes):
        iou = compute_iou(track_box, det_box)
        if iou > best_iou:
            best_iou = iou
            best_idx = i
    return best_idx if best_idx != -1 else None

def compute_iou(boxA, boxB):
    xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
    xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    areaA = max(1e-5, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    areaB = max(1e-5, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))
    return inter / (areaA + areaB - inter + 1e-5)

# The inference callback
def inference_callback(completion_info, bindings_list, input_batch, output_queue):
    if completion_info.exception:
        logger.error(f'Inference error: {completion_info.exception}')
    else:
        for i, bindings in enumerate(bindings_list):
            if len(bindings._output_names) == 1:
                result = bindings.output().get_buffer()
            else:
                result = {
                    name: np.expand_dims(bindings.output(name).get_buffer(), axis=0)
                    for name in bindings._output_names
                }
            output_queue.put((input_batch[i], result))

frame_counter = [0]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detection Example")
    parser.add_argument("-n", "--net", help="Path for the network in HEF format.",
                        default="yolov8n.hef")
    parser.add_argument("-i", "--input", default="camera",
                        help="Path to the input - 'camera' for live PiCamera.")
    parser.add_argument("-b", "--batch_size", default=1, type=int, required=False,
                        help="Number of images in one batch")
    parser.add_argument("-l", "--labels",
                        default=str(Path(__file__).parent.parent / "common" / "coco.txt"),
                        help="Path to a text file containing labels. If no labels file is provided, coco2017 will be used.")
    parser.add_argument("-s", "--save_stream_output", action="store_true",
                        help="Save the output of the inference from a stream.")
    parser.add_argument("-o", "--output-dir", help="Directory to save the results.",
                        default=None)
    parser.add_argument("-r", "--resolution", choices=["sd", "hd", "fhd"], default="sd",
                        help="Choose input resolution: 'sd' (640x480), 'hd' (1280x720), or 'fhd' (1920x1080). Default is 'sd'.")
    parser.add_argument("--track", action="store_true",
                        help="Enable object tracking across frames.")
    parser.add_argument("--show-fps", action="store_true",
                        help="Enable FPS performance measurement.")
    args = parser.parse_args()
    if not os.path.exists(args.net):
        raise FileNotFoundError(f"Network file not found: {args.net}")
    if not os.path.exists(args.labels):
        raise FileNotFoundError(f"Labels file not found: {args.labels}")
    if args.output_dir is None:
        args.output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(args.output_dir, exist_ok=True)
    return args

def infer(net, input_source, batch_size, labels, output_dir,
          save_stream_output=False, resolution="sd",
          enable_tracking=False, show_fps=False) -> None:
    labels = get_labels(labels)
    config_data = load_json_file("config.json")

    cap, images = init_input_source(input_source, batch_size, resolution)
    tracker = None
    if enable_tracking:
        tracker_config = config_data.get("visualization_params", {}).get("tracker", {})
        tracker = BYTETracker(SimpleNamespace(**tracker_config))

    input_queue = queue.Queue()
    output_queue = queue.Queue()

    post_process_callback_fn = partial(
        inference_result_handler, labels=labels,
        config_data=config_data, tracker=tracker
    )
    inference_callback_fn = partial(
        inference_callback, output_queue=output_queue
    )

    hailo_inference = HailoAsyncInference(
        net, input_queue, inference_callback_fn,
        batch_size, send_original_frame=True
    )
    height, width, _ = hailo_inference.get_input_shape()

    preprocess_thread = threading.Thread(
        target=preprocess, args=(images, cap, batch_size, input_queue, width, height)
    )
    postprocess_thread = threading.Thread(
        target=visualize, args=(output_queue, cap, save_stream_output,
                               output_dir, post_process_callback_fn, frame_counter)
    )

    if show_fps:
        start_time = time.time()

    preprocess_thread.start()
    postprocess_thread.start()
    hailo_inference.run()

    preprocess_thread.join()
    output_queue.put(None)  # Signal process thread to exit
    postprocess_thread.join()

    logger.info('Inference was successful!')

    if show_fps:
        end_time = time.time()
        fps = frame_counter[0] / (end_time - start_time)
        logger.debug(f"Processed {frame_counter[0]} frames at {fps:.2f} FPS")

def main() -> None:
    args = parse_args()
    infer(args.net, args.input, args.batch_size, args.labels,
          args.output_dir, args.save_stream_output, args.resolution,
          args.track, args.show_fps)

if __name__ == "__main__":
    main()

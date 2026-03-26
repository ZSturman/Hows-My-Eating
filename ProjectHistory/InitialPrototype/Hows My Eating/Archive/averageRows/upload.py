import cv2
import dlib
import numpy as np
import json
import argparse
import os
from time import time

# -------------------------------
# Utility Functions and Constants
# -------------------------------

# Load the pre-trained facial landmark detector.
predictor_path = "shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

def calculate_ratios(landmarks):
    """
    Calculate various ratios from the 68-landmark facial points.
    Returned keys:
      - feat_between_lips_to_mouth_width: (vertical lip gap / mouth width)
      - feat_nose_to_lips_lips_to_chin: (lip gap / chin-to-nose distance)
      - feat_mouth_width_outside_lips: (mouth width / chin-to-nose distance)
      - feat_top_lip_height_to_mouth_width: (top lip thickness / mouth width)
      - feat_bottom_lip_height_to_mouth_width: (bottom lip thickness / mouth width)
      - feat_mouth_width_inside_lips: (inner mouth width / mouth width)
      - feat_mouth_width_nose_to_chin: (same as outside lips in this example)
      - mouth_open_ratio: (here defined as lips_height/mouth_width)
    """
    ratios = {}
    mouth_width = np.linalg.norm(landmarks[48] - landmarks[54])
    lips_height = np.linalg.norm(landmarks[51] - landmarks[57])
    chin_to_nose = np.linalg.norm(landmarks[8] - landmarks[33])
    
    ratios["feat_between_lips_to_mouth_width"] = lips_height / mouth_width if mouth_width else 0
    ratios["feat_nose_to_lips_lips_to_chin"] = lips_height / chin_to_nose if chin_to_nose else 0
    ratios["feat_mouth_width_outside_lips"] = mouth_width / chin_to_nose if chin_to_nose else 0

    top_lip_height = np.linalg.norm(landmarks[51] - landmarks[62])
    ratios["feat_top_lip_height_to_mouth_width"] = top_lip_height / mouth_width if mouth_width else 0
    bottom_lip_height = np.linalg.norm(landmarks[57] - landmarks[66])
    ratios["feat_bottom_lip_height_to_mouth_width"] = bottom_lip_height / mouth_width if mouth_width else 0
    mouth_width_inside = np.linalg.norm(landmarks[60] - landmarks[64])
    ratios["feat_mouth_width_inside_lips"] = mouth_width_inside / mouth_width if mouth_width else 0
    ratios["feat_mouth_width_nose_to_chin"] = ratios["feat_mouth_width_outside_lips"]
    ratios["mouth_open_ratio"] = ratios["feat_between_lips_to_mouth_width"]

    return ratios

def draw_feature_lines(frame, landmarks):
    """Draw key feature lines (mouth width, lip gap, and chin-to-nose) on the frame."""
    cv2.line(frame, tuple(landmarks[48]), tuple(landmarks[54]), (0, 255, 0), 2)
    cv2.line(frame, tuple(landmarks[51]), tuple(landmarks[57]), (255, 0, 0), 2)
    cv2.line(frame, tuple(landmarks[8]), tuple(landmarks[33]), (0, 0, 255), 2)

def predict_mouth_state(ratios, threshold=0.3):
    """
    Predict the mouth state ("Open" or "Closed") based on the mouth_open_ratio.
    """
    return "Open" if ratios.get("mouth_open_ratio", 0) >= threshold else "Closed"

# Detection functions

def detect_chew_pattern_frames(sample_buffer, closed_threshold=0.3, open_threshold=0.5,
                               min_open_frames=30, max_open_frames=80, closed_frames=2):
    """
    Detect a chew pattern using a sliding window measured in frame count.
    sample_buffer is a list of tuples (frame_index, ratios) for consecutive frames.
    Returns a tuple (chew_detected, total_frame_count).
    """
    total_frames = len(sample_buffer)
    min_total = closed_frames * 2 + min_open_frames
    max_total = closed_frames * 2 + max_open_frames

    if total_frames < min_total or total_frames > max_total:
        return False, total_frames

    first_part = [r["mouth_open_ratio"] for (_, r) in sample_buffer[:closed_frames]]
    last_part = [r["mouth_open_ratio"] for (_, r) in sample_buffer[-closed_frames:]]
    middle_part = [r["mouth_open_ratio"] for (_, r) in sample_buffer[closed_frames:-closed_frames]]

    avg_first = sum(first_part) / len(first_part)
    avg_last = sum(last_part) / len(last_part)
    max_middle = max(middle_part) if middle_part else 0

    if avg_first < closed_threshold and avg_last < closed_threshold and max_middle >= open_threshold:
        return True, total_frames
    return False, total_frames

def detect_chew_pattern(sample_buffer, closed_threshold=0.3, open_threshold=0.5,
                        min_duration=0.2, max_duration=0.8):
    """
    Detect a chew pattern using a sliding window measured in time.
    Expects sample_buffer to be a list of (timestamp, ratios).
    Returns a tuple (chew_detected, window_duration).
    """
    duration = sample_buffer[-1][0] - sample_buffer[0][0]
    if duration < min_duration or duration > max_duration:
        return False, duration
    n = len(sample_buffer)
    if n < 3:
        return False, duration
    # Use first and last 10% for "closed" state and the middle for "open" state.
    first_count = max(1, n // 10)
    last_count = max(1, n // 10)
    first_part = [r["mouth_open_ratio"] for (_, r) in sample_buffer[:first_count]]
    last_part = [r["mouth_open_ratio"] for (_, r) in sample_buffer[-last_count:]]
    middle_part = [r["mouth_open_ratio"] for (_, r) in sample_buffer[first_count:n-last_count]]
    avg_first = sum(first_part) / len(first_part)
    avg_last = sum(last_part) / len(last_part)
    max_middle = max(middle_part) if middle_part else 0
    if avg_first < closed_threshold and avg_last < closed_threshold and max_middle >= open_threshold:
        return True, duration
    return False, duration

# -------------------------------
# Rotation Helpers
# -------------------------------

def detect_face_with_rotation(frame, detector):
    """
    Try detecting a face on the given frame with various rotations.
    Returns a tuple (faces, rotation_code, oriented_frame) where rotation_code:
      0 = no rotation
      1 = 90° clockwise
      2 = 180° rotation
      3 = 90° counter-clockwise
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    if faces:
        return faces, 0, frame

    rotated = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    gray_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    faces = detector(gray_rotated)
    if faces:
        return faces, 1, rotated

    rotated = cv2.rotate(frame, cv2.ROTATE_180)
    gray_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    faces = detector(gray_rotated)
    if faces:
        return faces, 2, rotated

    rotated = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    gray_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    faces = detector(gray_rotated)
    if faces:
        return faces, 3, rotated

    return None, 0, frame

def apply_rotation(frame, rotation_code):
    """
    Apply a specific rotation to the frame based on rotation_code.
    """
    if rotation_code == 0:
        return frame
    elif rotation_code == 1:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_code == 2:
        return cv2.rotate(frame, cv2.ROTATE_180)
    elif rotation_code == 3:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame

# -------------------------------
# Main Video Processing Function (Multiple Schemes)
# -------------------------------

def process_video_multiple(input_video_path, output_video_path, output_json_path):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Could not open video file:", input_video_path)
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Determine orientation using the 30th frame.
    cap.set(cv2.CAP_PROP_POS_FRAMES, 30)
    ret, frame_30 = cap.read()
    if not ret:
        print("Error: Could not read the 30th frame")
        return

    faces, rotation_code, _ = detect_face_with_rotation(frame_30, detector)
    if not faces:
        print("No face detected in the 30th frame; cannot determine correct orientation.")
        return

    print(f"Orientation determined using the 30th frame: Rotation code = {rotation_code}")

    # Rewind to the first frame.
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, first_frame = cap.read()
    if not ret:
        print("Error: Could not read the first frame")
        return

    oriented_first_frame = apply_rotation(first_frame, rotation_code)
    height, width = oriented_first_frame.shape[:2]
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Define detection schemes. Each scheme uses either time or frame based sliding window.
    detection_schemes = [
        {
            "name": "Time_2",
            "method": "time",
            "params": {"closed_threshold": 0.35, "open_threshold": 0.5, "min_duration": 0.15, "max_duration": 1.0},
            "prev_state": "Not Chew",
            "chew_count": 0
        },
    ]

    # Initialize two sliding windows: one for time-based and one for frame-based detection.
    sliding_window_time = []   # entries: (timestamp, ratios)
    sliding_window_frame = []  # entries: (frame_index, ratios)

    detection_results = []  # will store the detection data per frame

    # Variables to track mouth state transitions.
    prev_mouth_state = None
    closed_to_open_predictions = []
    open_to_closed_predictions = []

    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = apply_rotation(frame, rotation_code)
        timestamp = frame_index / fps
        frame_index += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        if faces:
            face = faces[0]
            landmarks_dlib = predictor(gray, face)
            landmarks = np.array([[p.x, p.y] for p in landmarks_dlib.parts()])
            ratios = calculate_ratios(landmarks)
            draw_feature_lines(frame, landmarks)
            # Append current sample to both sliding windows.
            sliding_window_time.append((timestamp, ratios))
            sliding_window_frame.append((frame_index, ratios))
            
            # Use a simple threshold to determine an overall mouth state.
            mouth_ratio = ratios.get("mouth_open_ratio", 0)
            if mouth_ratio >= 0.5:
                current_state = "Open"
            elif mouth_ratio <= 0.3:
                current_state = "Closed"
            else:
                current_state = prev_mouth_state if prev_mouth_state is not None else "Closed"
            
            # Check for state transitions if previous state is available and valid.
            if prev_mouth_state is not None and prev_mouth_state in ["Closed", "Open"] and current_state in ["Closed", "Open"]:
                if prev_mouth_state == "Closed" and current_state == "Open":
                    closed_to_open_predictions.append({
                        "frame_index": frame_index,
                        "timestamp": timestamp,
                        "prediction": "Closed to Open"
                    })
                    print(f"Frame {frame_index}: Closed to Open transition detected.")
                elif prev_mouth_state == "Open" and current_state == "Closed":
                    open_to_closed_predictions.append({
                        "frame_index": frame_index,
                        "timestamp": timestamp,
                        "prediction": "Open to Closed"
                    })
                    print(f"Frame {frame_index}: Open to Closed transition detected.")
            
            prev_mouth_state = current_state
            current_mouth_state = current_state
        else:
            current_mouth_state = "No Face"

        # Prune the sliding windows:
        # For the time-based window, remove entries older than the maximum duration among time schemes.
        max_window_duration_time = max(
            [scheme["params"]["max_duration"] for scheme in detection_schemes if scheme["method"] == "time"],
            default=0
        )
        while sliding_window_time and (timestamp - sliding_window_time[0][0] > max_window_duration_time):
            sliding_window_time.pop(0)
        
        # For the frame-based window, remove entries if the total count exceeds the maximum total frames among frame schemes.
        max_total_frames = max(
            [scheme["params"].get("closed_frames", 0) * 2 + scheme["params"].get("max_open_frames", 0) for scheme in detection_schemes if scheme["method"] == "frame"],
            default=0
        )
        while len(sliding_window_frame) > max_total_frames:
            sliding_window_frame.pop(0)
        
        # Evaluate each detection scheme.
        scheme_results = {}
        for scheme in detection_schemes:
            if scheme["method"] == "time":
                if sliding_window_time and (timestamp - sliding_window_time[0][0] >= scheme["params"]["min_duration"]):
                    detected, value = detect_chew_pattern(
                        sliding_window_time,
                        closed_threshold=scheme["params"]["closed_threshold"],
                        open_threshold=scheme["params"]["open_threshold"],
                        min_duration=scheme["params"]["min_duration"],
                        max_duration=scheme["params"]["max_duration"]
                    )
                    result = "Chew" if detected else "Not Chew"
                    window_metric = value  # duration in seconds
                else:
                    result = "N/A"
                    window_metric = 0.0
            elif scheme["method"] == "frame":
                min_total = scheme["params"]["closed_frames"] * 2 + scheme["params"]["min_open_frames"]
                if len(sliding_window_frame) >= min_total:
                    detected, value = detect_chew_pattern_frames(
                        sliding_window_frame,
                        closed_threshold=scheme["params"]["closed_threshold"],
                        open_threshold=scheme["params"]["open_threshold"],
                        min_open_frames=scheme["params"]["min_open_frames"],
                        max_open_frames=scheme["params"]["max_open_frames"],
                        closed_frames=scheme["params"]["closed_frames"]
                    )
                    result = "Chew" if detected else "Not Chew"
                    window_metric = value  # total frame count of the window
                else:
                    result = "N/A"
                    window_metric = 0
            else:
                result = "N/A"
                window_metric = None

            # Increment the counter if there is a transition from a non-chew state to a chew state.
            if scheme["prev_state"] != "Chew" and result == "Chew":
                scheme["chew_count"] += 1
            scheme["prev_state"] = result

            scheme_results[scheme["name"]] = {
                "result": result,
                "window_metric": window_metric,
                "chew_count": scheme["chew_count"]
            }

        # Prepare overlay text lines.
        overlay_lines = [
            f"Frame: {frame_index}/{total_frames}, Time: {timestamp:.2f}s",
            f"Mouth State: {current_mouth_state}"
        ]
        for scheme_name, res in scheme_results.items():
            overlay_lines.append(f"{scheme_name}: {res['result']} (Metric: {res['window_metric']}, Count: {res['chew_count']})")
        overlay_lines.append(f"Closed->Open Transitions: {len(closed_to_open_predictions)}")
        overlay_lines.append(f"Open->Closed Transitions: {len(open_to_closed_predictions)}")

        # Display each overlay line on the frame.
        for i, line in enumerate(overlay_lines):
            y = 60 + i * 30
            # Background rectangle for improved text readability
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.rectangle(frame, (15, y - 20), (15 + text_size[0] + 10, y + 10), (0, 0, 0), -1)
            # Render text with improved size, color, and thickness
            cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Log the detection result for this frame.
        detection_results.append({
            "frame_index": frame_index,
            "timestamp": timestamp,
            "mouth_state": current_mouth_state,
            "schemes": scheme_results
        })

        print(f"Processing frame {frame_index}/{total_frames} - Time: {timestamp:.2f}s")
        out.write(frame)

    cap.release()
    out.release()

    with open(output_json_path, "w") as f:
        json.dump(detection_results, f, indent=4)

    print(f"Processing complete. Output video saved as {output_video_path}")
    print(f"Detection metadata saved as {output_json_path}")

# -------------------------------
# Command-Line Argument Parsing
# -------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a video file for chew and mouth state detection using multiple schemes.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input video file.")
    parser.add_argument("--output_video", type=str, default="output_video.mp4", help="Path for the output annotated video.")
    parser.add_argument("--output_json", type=str, default="detections.json", help="Path for the output JSON metadata file.")
    args = parser.parse_args()

    process_video_multiple(args.input, args.output_video, args.output_json)
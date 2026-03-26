import cv2
import dlib
import numpy as np
from time import time, sleep

# Load the pre-trained facial landmark detector
predictor_path = "shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

# --- Feature Calculation ---
def calculate_ratios(landmarks):
    """
    Calculate various ratios from the 68-landmark facial points.
    The returned dictionary includes:
      - feat_between_lips_to_mouth_width: vertical lip gap / mouth width
      - feat_nose_to_lips_lips_to_chin: lip gap / (chin-to-nose distance)
      - feat_mouth_width_outside_lips: mouth width / (chin-to-nose distance)
      - feat_top_lip_height_to_mouth_width: top lip thickness / mouth width
      - feat_bottom_lip_height_to_mouth_width: bottom lip thickness / mouth width
      - feat_mouth_width_inside_lips: inner mouth width / mouth width
      - feat_mouth_width_nose_to_chin: same as outside lips in this example
      - mouth_open_ratio: here defined as (lips height / mouth width)
    """
    ratios = {}
    # Outer mouth corners: points 48 and 54
    mouth_width = np.linalg.norm(landmarks[48] - landmarks[54])
    # Vertical gap between upper and lower outer lip: points 51 and 57
    lips_height = np.linalg.norm(landmarks[51] - landmarks[57])
    # Distance from nose (point 33) to chin (point 8)
    chin_to_nose = np.linalg.norm(landmarks[8] - landmarks[33])
    
    ratios["feat_between_lips_to_mouth_width"] = lips_height / mouth_width if mouth_width else 0
    ratios["feat_nose_to_lips_lips_to_chin"] = lips_height / chin_to_nose if chin_to_nose else 0
    ratios["feat_mouth_width_outside_lips"] = mouth_width / chin_to_nose if chin_to_nose else 0
    
    # Additional features:
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
    """Draw lines between key points for visualization."""
    cv2.line(frame, tuple(landmarks[48]), tuple(landmarks[54]), (0, 255, 0), 2)  # Mouth width
    cv2.line(frame, tuple(landmarks[51]), tuple(landmarks[57]), (255, 0, 0), 2)  # Lips height
    cv2.line(frame, tuple(landmarks[8]), tuple(landmarks[33]), (0, 0, 255), 2)   # Chin-to-nose

# --- New Chew Detection Based on Mouth Pattern ---
def detect_chew_pattern(sample_buffer, closed_threshold=0.3, open_threshold=0.5,
                        min_duration=0.2, max_duration=0.8):
    """
    Look for a closed -> open -> closed pattern in the mouth_open_ratio.
    
    The function assumes:
      - The mouth is "closed" when mouth_open_ratio is below closed_threshold.
      - The mouth is "open" when mouth_open_ratio is at or above open_threshold.
      
    The function returns a tuple (chew_detected, duration), where:
      - chew_detected is True if:
          * The first sample's ratio is below closed_threshold (closed),
          * At least one sample in the window has a ratio >= open_threshold (open),
          * The last sample's ratio is below closed_threshold (closed), and
          * The total duration is between min_duration and max_duration seconds.
      - duration is the total time from the first to the last sample.
      
    To update the values for open and closed ratios, adjust closed_threshold and open_threshold.
    For example, if your data indicates that a closed mouth always has a ratio below 0.3,
    then leave closed_threshold as 0.3. If an open mouth typically has a ratio above 0.5,
    set open_threshold to 0.5.
    """
    if not sample_buffer:
        return False, 0.0
    
    start_time, first_ratios = sample_buffer[0]
    end_time, last_ratios = sample_buffer[-1]
    duration = end_time - start_time
    
    # Check if total duration is within the desired timeframe.
    if duration < min_duration or duration > max_duration:
        return False, duration
    
    # Check if the mouth is closed at the beginning and end.
    if first_ratios.get("mouth_open_ratio", 0) >= closed_threshold:
        return False, duration
    if last_ratios.get("mouth_open_ratio", 0) >= closed_threshold:
        return False, duration
    
    # Find the maximum mouth_open_ratio during the window.
    max_ratio = max(r.get("mouth_open_ratio", 0) for _, r in sample_buffer)
    if max_ratio >= open_threshold:
        return True, duration
    
    return False, duration

def predict_mouth_state(ratios, threshold=0.3):
    """
    Predict the mouth state ("Open" vs "Closed") based on the computed mouth_open_ratio.
    
    You can update the threshold value here if your data shows that the ratio for an open mouth
    is higher or lower than the default threshold (0.3).
    """
    return "Open" if ratios.get("mouth_open_ratio", 0) >= threshold else "Closed"

# --- Global Variables for Overlay Feedback ---
last_chew_prediction = "N/A"
last_chew_duration = 0.0
last_mouth_state = "N/A"
last_mouth_ratio = 0.0

# We'll accumulate facial feature measurements over a short window.
sample_buffer = []  # each element: (timestamp, ratios)

# --- Video Capture Loop ---
cap = cv2.VideoCapture(1)  # Use the appropriate camera (or video file)
fps = cap.get(cv2.CAP_PROP_FPS)
min_window_duration = 0.2  # We use the lower bound of the chewing timeframe

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    # Process only the first detected face.
    if faces:
        face = faces[0]
        landmarks_dlib = predictor(gray, face)
        landmarks = np.array([[p.x, p.y] for p in landmarks_dlib.parts()])
        
        # Compute ratios for this frame.
        ratios = calculate_ratios(landmarks)
        draw_feature_lines(frame, landmarks)
        
        # Append the measurement (timestamp and ratios) to the buffer.
        sample_buffer.append((current_time, ratios))
    
    # When there is enough data in the buffer, try to detect a chew pattern.
    if sample_buffer:
        # Use the total duration of the buffer.
        window_duration = sample_buffer[-1][0] - sample_buffer[0][0]
        # We only process if the window duration is at least the lower bound (min_duration).
        if window_duration >= min_window_duration:
            chew_detected, duration = detect_chew_pattern(sample_buffer,
                                                          closed_threshold=0.3,  # Update this value if needed.
                                                          open_threshold=0.5,    # Update this value if needed.
                                                          min_duration=0.2,
                                                          max_duration=0.8)
            chew_prediction = "Chew" if chew_detected else "Not Chew"
            last_chew_prediction = chew_prediction
            last_chew_duration = duration
            # Clear the buffer after processing to start a new detection window.
            sample_buffer = []
    
    # For mouth state, we use the most recent measurement.
    if faces:
        last_mouth_state = predict_mouth_state(ratios, threshold=0.3)  # Adjust threshold if needed.
        last_mouth_ratio = ratios.get("mouth_open_ratio", 0)
    
    # Overlay the computed predictions on the frame.
    overlay_lines = [
        f"Chew Prediction: {last_chew_prediction} (duration: {last_chew_duration:.2f}s)",
        f"Mouth State: {last_mouth_state} (ratio: {last_mouth_ratio:.2f})"
    ]
    for i, text in enumerate(overlay_lines):
        y_position = 30 + i * 30
        # Use green text for positive predictions and red for negative.
        if i == 0:
            color = (0, 255, 0) if last_chew_prediction == "Chew" else (0, 0, 255)
        elif i == 1:
            color = (0, 255, 0) if last_mouth_state == "Open" else (0, 0, 255)
        else:
            color = (255, 255, 255)
        cv2.putText(frame, text, (10, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
import os
import warnings
import json
import sys
import cv2
import dlib
import numpy as np
import mediapipe as mp
import pandas as pd
import math

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import absl.logging
absl.logging.set_verbosity('error')

warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")

# Load facial landmark detector
print("Loading facial landmark detector...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
print("Facial landmark detector loaded.")

# Initialize MediaPipe hands
print("Initializing MediaPipe hands...")
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)
print("MediaPipe hands initialized.")

def detect_hand(frame):
    hands_detected = []
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            hands_detected.append(hand_landmarks)
    
    return hands_detected

def extract_face_landmarks(landmarks):
    all_points = [landmarks.part(i) for i in range(68)]
    coordinates = np.array([(p.x, p.y) for p in all_points])
    return coordinates

def calculate_face_orientation(landmarks, frame):
    model_points = np.array([
        (0.0, 0.0, 0.0),          
        (0.0, -330.0, -65.0),     
        (-225.0, 170.0, -135.0),  
        (225.0, 170.0, -135.0),   
        (-150.0, -150.0, -125.0), 
        (150.0, -150.0, -125.0)   
    ], dtype=np.float64)

    image_points = np.array([
        (landmarks.part(30).x, landmarks.part(30).y),     
        (landmarks.part(8).x, landmarks.part(8).y),       
        (landmarks.part(36).x, landmarks.part(36).y),     
        (landmarks.part(45).x, landmarks.part(45).y),     
        (landmarks.part(48).x, landmarks.part(48).y),     
        (landmarks.part(54).x, landmarks.part(54).y)      
    ], dtype=np.float64)

    size = (frame.shape[1], frame.shape[0])
    focal_length = size[1]
    center = (size[1] / 2, size[0] / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")

    dist_coeffs = np.zeros((4, 1))

    success, rotation_vector, translation_vector = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs)
    rmat, _ = cv2.Rodrigues(rotation_vector)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
    pitch, yaw, roll = [math.degrees(angle) for angle in angles]

    return pitch, yaw, roll

def get_hand_hull(hand_landmarks, frame_size):
    hand_points = [(int(lm.x * frame_size[0]), int(lm.y * frame_size[1])) for lm in hand_landmarks.landmark]
    points_array = np.array(hand_points, np.int32)
    
    if len(points_array) > 0:
        hull = cv2.convexHull(points_array)
        hull_points = hull.squeeze().tolist() if len(hull) > 0 else []
    else:
        hull_points = []
    
    return hull_points

def process_video(file_path):
    print(f"Opening video file: {file_path}...")
    cap = cv2.VideoCapture(file_path)
    frame_count = 0
    data = []

    if not cap.isOpened():
        print(json.dumps({"status": "error", "message": "Could not open video."}))
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(json.dumps({"status": "processing", "total_frames": total_frames}))

    head_detected = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        timestamp = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 4)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        hands_detected = detect_hand(frame)

        row_data = {
            "Frame": frame_count,
            "Timestamp": timestamp,
            "Pitch": None,
            "Yaw": None,
            "Roll": None
        }

        # Initialize columns for jaw points (1-17), mouth points (49-68), and hand hull points
        for i in range(1, 18):
            row_data[f"Point_{i}_x"] = -1
            row_data[f"Point_{i}_y"] = -1
        for i in range(49, 69):
            row_data[f"Point_{i}_x"] = -1
            row_data[f"Point_{i}_y"] = -1
        for i in range(21):  # Assuming up to 21 points in hand hull
            row_data[f"Hand_{i}_x"] = -1
            row_data[f"Hand_{i}_y"] = -1

        if faces:
            head_detected = True
            for face in faces:
                landmarks = predictor(gray, face)
                all_points = extract_face_landmarks(landmarks)
                pitch, yaw, roll = calculate_face_orientation(landmarks, frame)

                row_data["Pitch"] = pitch
                row_data["Yaw"] = yaw
                row_data["Roll"] = roll

                # Update jaw and mouth points
                for i in range(1, 18):
                    row_data[f"Point_{i}_x"] = all_points[i - 1][0]
                    row_data[f"Point_{i}_y"] = all_points[i - 1][1]
                for i in range(49, 69):
                    row_data[f"Point_{i}_x"] = all_points[i - 1][0]
                    row_data[f"Point_{i}_y"] = all_points[i - 1][1]

        if hands_detected:
            # Record the convex hull of the detected hand
            hand_hull_points = get_hand_hull(hands_detected[0], frame.shape)
            for i, (x, y) in enumerate(hand_hull_points):
                if i < 21:  # Limit to the first 21 points of the hull
                    row_data[f"Hand_{i}_x"] = x
                    row_data[f"Hand_{i}_y"] = y

        data.append(row_data)

        progress = round((frame_count / total_frames) * 100, 2)
        print(json.dumps({"status": "processing", "progress": progress}))

    cap.release()
    cv2.destroyAllWindows()

    print(json.dumps({"status": "completed", "message": "Processing complete."}))

    df = pd.DataFrame(data)
    df.to_csv("features.csv", index=False)
    print(json.dumps({"status": "completed", "message": "Data saved to features.csv"}))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: get_mov_info.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    process_video(file_path)
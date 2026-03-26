""" import os
import warnings
import json
import sys
import cv2
import dlib
import numpy as np
import mediapipe as mp
import pandas as pd
import math
import argparse

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

# Initialize states and actions
mouth_state = "CLOSED"
mouth_action = ""
is_eating = False
is_talking = False
frame_skip = 1  # Initialize frame skip

def initialize_video_writers(frame_size, fps):
    fourcc = cv2.VideoWriter_fourcc(*'vp80')
    nose_writer = cv2.VideoWriter('nose_points.webm', fourcc, fps, frame_size, True)
    jawline_writer = cv2.VideoWriter('jawline_points.webm', fourcc, fps, frame_size, True)
    lips_writer = cv2.VideoWriter('lips_points.webm', fourcc, fps, frame_size, True)
    eyes_writer = cv2.VideoWriter('eyes_points.webm', fourcc, fps, frame_size, True)
    hand_writer = cv2.VideoWriter('hand_points.webm', fourcc, fps, frame_size, True)
    return nose_writer, jawline_writer, lips_writer, eyes_writer, hand_writer

def detect_hand(frame):
    hands_detected = []
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            hands_detected.append(hand_landmarks)
    
    return hands_detected

def extract_face_landmarks(landmarks):
    jawline_points = [landmarks.part(i) for i in range(0, 17)]
    lips_points = [landmarks.part(i) for i in range(48, 68)]
    
    jawline_coordinates = np.array([(p.x, p.y) for p in jawline_points])
    lips_coordinates = np.array([(p.x, p.y) for p in lips_points])
    
    return jawline_coordinates, lips_coordinates

def extract_hand_points(hand_landmarks):
    hand_coordinates = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
    return hand_coordinates

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

def draw_points(frame, points, color=(0, 255, 0)):
    for point in points:
        cv2.circle(frame, (int(point[0]), int(point[1])), 2, color, -1)

def draw_labels_on_frame(frame, frame_count, total_frames):
    # Background rectangles for better readability
    cv2.rectangle(frame, (5, 10), (250, 160), (0, 0, 0), -1)

    # Display the current labels and frame info on the frame
    cv2.putText(frame, f"Frame: {frame_count}/{total_frames}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"MouthState: {mouth_state}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"MouthAction: {mouth_action}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"isEating: {is_eating}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"isTalking: {is_talking}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

def process_video(file_path):
    global mouth_state, mouth_action, is_eating, is_talking, frame_skip
    
    print(f"Opening video file: {file_path}...")
    cap = cv2.VideoCapture(file_path)
    frame_count = 0
    data = []

    if not cap.isOpened():
        print(json.dumps({"status": "error", "message": "Could not open video."}))
        return

    fps = 30
    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    
    nose_writer, jawline_writer, lips_writer, eyes_writer, hand_writer = initialize_video_writers(frame_size, fps)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(json.dumps({"status": "processing", "total_frames": total_frames}))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        timestamp = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 4)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        hands_detected = detect_hand(frame)

        for face in faces:
            landmarks = predictor(gray, face)
            jawline, lips = extract_face_landmarks(landmarks)
            pitch, yaw, roll = calculate_face_orientation(landmarks, frame)

            jawline_frame = np.zeros_like(frame)
            lips_frame = np.zeros_like(frame)
            hand_frame = np.zeros_like(frame)

            draw_points(jawline_frame, jawline)
            draw_points(lips_frame, lips)

            if hands_detected:
                hand_points = extract_hand_points(hands_detected[0])
                draw_points(hand_frame, [(int(p[0] * frame_size[0]), int(p[1] * frame_size[1])) for p in hand_points])
            else:
                hand_points = []

            row_data = {
                "Frame": frame_count,
                "Timestamp": timestamp,
                "Jawline Points": jawline.flatten().tolist() if len(jawline) > 0 else [0] * 34,
                "Lips Points": lips.flatten().tolist() if len(lips) > 0 else [0] * 40,
                "Pitch": pitch,
                "Yaw": yaw,
                "Roll": roll,
                "Hand Points": [item for sublist in hand_points for item in sublist],
                "MouthState": mouth_state,
                "MouthAction": mouth_action,
                "isEating": is_eating,
                "isTalking": is_talking
            }
            data.append(row_data)

            jawline_writer.write(jawline_frame)
            lips_writer.write(lips_frame)
            hand_writer.write(hand_frame)

        draw_labels_on_frame(frame, frame_count, total_frames)  # Display labels on the frame
        cv2.imshow('Frame', frame)
        
        # Only pause on every other frame
        if frame_count % 2 == 0:
            while True:
                key = cv2.waitKey(0) & 0xFF
                if key == ord('\r') or key == ord('\n'):  # Enter key
                    break
                elif key == ord(' '):  # Reset MouthAction
                    mouth_action = ""
                elif key == ord('e'):  # Toggle isEating
                    is_eating = not is_eating
                elif key == ord('t'):  # Toggle isTalking
                    is_talking = not is_talking
                elif key == ord('d'):
                    mouth_action = "DRINKING"
                elif key == ord('l'):
                    mouth_action = "LAUGHING"
                elif key == ord('y'):
                    mouth_action = "YAWNING"
                elif key == ord('b'):
                    mouth_action = "BITING"
                elif key == ord('c'):  # 'c' for CHEWING
                    mouth_action = "CHEWING"
                elif key == ord('o'):  # 'o' for OPEN
                    mouth_state = "OPEN"
                elif key == ord('x'):  # 'x' for CLOSED
                    mouth_state = "CLOSED"
                elif key == ord('p'):  # 'p' for OPENING
                    mouth_state = "OPENING"
                elif key == ord('g'):  # 'g' for CLOSING
                    mouth_state = "CLOSING"
                elif key == ord('q'):  # Quit
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                # Handle frame skipping keys
                elif key == ord('1'):
                    frame_skip = 1
                elif key == ord('2'):
                    frame_skip = 2
                elif key == ord('3'):
                    frame_skip = 4
                elif key == ord('4'):
                    frame_skip = 8
                elif key == ord('5'):
                    frame_skip = 16
                elif key == ord('6'):
                    frame_skip = 32
                elif key == ord('7'):
                    frame_skip = 64
                elif key == ord('8'):
                    frame_skip = 128
                elif key == ord('9'):
                    frame_skip = 256
                elif key == ord('0'):
                    frame_skip = 512

                # Update frame with the current selection immediately
                draw_labels_on_frame(frame, frame_count, total_frames)
                cv2.imshow('Frame', frame)

        # Jump forward by frame_skip frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count + frame_skip - 1)
        frame_count += frame_skip - 1  # Adjust frame_count to account for the skipped frames

        progress = round((frame_count / total_frames) * 100, 2)
        print(json.dumps({"status": "processing", "progress": progress}))

    cap.release()
    nose_writer.release()
    jawline_writer.release()
    lips_writer.release()
    eyes_writer.release()
    hand_writer.release()
    cv2.destroyAllWindows()

    print(json.dumps({"status": "completed", "message": "Processing complete."}))

    df = pd.DataFrame(data)
    df.to_csv("output_data.csv", index=False)
    print(json.dumps({"status": "completed", "message": "Data saved to output_data.csv"}))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: get_mov_info.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    process_video(file_path) """
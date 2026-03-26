import os
import warnings
import json
import sys
import cv2
import dlib
import numpy as np
import mediapipe as mp

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

def initialize_video_writers(frame_size, fps):
    fourcc = cv2.VideoWriter_fourcc(*'vp80')
    combined_writer = cv2.VideoWriter('combined_output.webm', fourcc, fps, frame_size, True)
    jawline_writer = cv2.VideoWriter('jawline_points.webm', fourcc, fps, frame_size, True)
    lips_writer = cv2.VideoWriter('lips_points.webm', fourcc, fps, frame_size, True)
    hand_writer = cv2.VideoWriter('hand_outline.webm', fourcc, fps, frame_size, True)
    original_writer = cv2.VideoWriter('original_output.webm', fourcc, fps, (frame_size[0], frame_size[1]), True)
    return combined_writer, jawline_writer, lips_writer, hand_writer, original_writer

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

def draw_points(frame, points, color=(0, 255, 0), size=3):
    for point in points:
        cv2.circle(frame, (int(point[0]), int(point[1])), size, color, -1)

def draw_lines(frame, points, indices, color=(0, 255, 0), thickness=2):
    for i in range(len(indices) - 1):
        pt1 = tuple(points[indices[i]])
        pt2 = tuple(points[indices[i + 1]])
        cv2.line(frame, pt1, pt2, color, thickness)

def draw_hand_outline(frame, hand_landmarks, frame_size):
    hand_points = [(int(lm.x * frame_size[0]), int(lm.y * frame_size[1])) for lm in hand_landmarks.landmark]
    points_array = np.array(hand_points, np.int32)
    
    hull = cv2.convexHull(points_array)
    cv2.polylines(frame, [hull], isClosed=True, color=(0, 255, 0), thickness=2)

def process_video(file_path):
    print(f"Opening video file: {file_path}...")
    cap = cv2.VideoCapture(file_path)
    frame_count = 0

    if not cap.isOpened():
        print(json.dumps({"status": "error", "message": "Could not open video."}))
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    
    # Determine the cropping dimensions
    square_size = min(frame_size)  # Use the smaller dimension to determine square size

    combined_writer, jawline_writer, lips_writer, hand_writer, original_writer = initialize_video_writers((square_size, square_size), fps)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        hands_detected = detect_hand(frame)

        jawline_frame = np.zeros_like(frame)
        lips_frame = np.zeros_like(frame)
        hand_frame = np.zeros_like(frame)
        combined_frame = frame.copy()
        original_frame = frame.copy()  # Keep original frame for drawing landmarks

        if faces:
            for face in faces:
                landmarks = predictor(gray, face)
                all_points = extract_face_landmarks(landmarks)

                # Draw points and lines on frames
                draw_points(jawline_frame, all_points[:17], size=4)
                draw_points(lips_frame, all_points[48:68], size=4)
                draw_points(combined_frame, all_points, color=(255, 0, 0), size=4)
                draw_points(original_frame, all_points, color=(255, 0, 0), size=4)  # Overlay points on the original frame

                draw_lines(combined_frame, all_points, list(range(17)), color=(255, 0, 0), thickness=2)
                draw_lines(combined_frame, all_points, list(range(48, 68)), color=(0, 255, 0), thickness=2)

                draw_lines(original_frame, all_points, list(range(17)), color=(255, 0, 0), thickness=2)  # Overlay lines on original
                draw_lines(original_frame, all_points, list(range(48, 68)), color=(0, 255, 0), thickness=2)

        for hand_landmarks in hands_detected:
            draw_hand_outline(hand_frame, hand_landmarks, frame_size)
            draw_hand_outline(combined_frame, hand_landmarks, frame_size)
            draw_hand_outline(original_frame, hand_landmarks, frame_size)  # Overlay hand points on the original frame

        # Determine cropping for square output
        if frame_size[0] < frame_size[1]:  # Portrait mode
            start_y = (frame_size[1] - square_size) // 2
            cropped_combined = combined_frame[start_y:start_y + square_size, :]
            cropped_jawline = jawline_frame[start_y:start_y + square_size, :]
            cropped_lips = lips_frame[start_y:start_y + square_size, :]
            cropped_hand = hand_frame[start_y:start_y + square_size, :]
        else:  # Landscape mode
            start_x = (frame_size[0] - square_size) // 2
            cropped_combined = combined_frame[:, start_x:start_x + square_size]
            cropped_jawline = jawline_frame[:, start_x:start_x + square_size]
            cropped_lips = lips_frame[:, start_x:start_x + square_size]
            cropped_hand = hand_frame[:, start_x:start_x + square_size]

        # Resize all frames to maintain square dimensions
        resized_combined_frame = cv2.resize(cropped_combined, (square_size, square_size))
        resized_jawline_frame = cv2.resize(cropped_jawline, (square_size, square_size))
        resized_lips_frame = cv2.resize(cropped_lips, (square_size, square_size))
        resized_hand_frame = cv2.resize(cropped_hand, (square_size, square_size))

        # Write frames to respective outputs
        original_writer.write(original_frame)
        combined_writer.write(resized_combined_frame)
        jawline_writer.write(resized_jawline_frame)
        lips_writer.write(resized_lips_frame)
        hand_writer.write(resized_hand_frame)

        # Preview each frame during creation
        cv2.imshow('Original Frame (Uncropped with Landmarks)', original_frame)
        cv2.imshow('Combined Output (Square)', resized_combined_frame)
        cv2.imshow('Jawline Points (Square)', resized_jawline_frame)
        cv2.imshow('Lips Points (Square)', resized_lips_frame)
        cv2.imshow('Hand Outline (Square)', resized_hand_frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        progress = round((frame_count / int(cap.get(cv2.CAP_PROP_FRAME_COUNT))) * 100, 2)
        print(json.dumps({"status": "processing", "progress": progress}))

    cap.release()
    original_writer.release()
    combined_writer.release()
    jawline_writer.release()
    lips_writer.release()
    hand_writer.release()
    cv2.destroyAllWindows()

    print(json.dumps({"status": "completed", "message": "Processing complete."}))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: get_mov_info.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    process_video(file_path)
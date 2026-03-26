import sys
import os
import mediapipe as mp
import dlib

def resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource, handling PyInstaller's _MEIPASS temp directory."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    abs_path = os.path.join(base_path, relative_path)
    if not os.path.exists(abs_path):
        print(f"WARNING: Resource not found: {abs_path}")  # Debugging
    return abs_path

# Paths to resources
MODEL_PATH = resource_path("src/models/shape_predictor_68_face_landmarks.dat")
HAND_LANDMARK_TFLITE_PATH = resource_path("mediapipe/modules/hand_landmark/hand_landmark_full.tflite")
HAND_LANDMARK_BINARYPB_PATH = resource_path("mediapipe/modules/hand_landmark/hand_landmark_tracking_cpu.binarypb")
PALM_DETECTION_TFLITE_PATH = resource_path("mediapipe/modules/palm_detection/palm_detection_full.tflite")

def get_mediapipe_hands():
    """Initialize Mediapipe Hands module with the correct model paths."""
    return mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        model_complexity=1
    )

def get_dlib_detector():
    return dlib.get_frontal_face_detector()

def get_dlib_predictor():
    return dlib.shape_predictor(MODEL_PATH)
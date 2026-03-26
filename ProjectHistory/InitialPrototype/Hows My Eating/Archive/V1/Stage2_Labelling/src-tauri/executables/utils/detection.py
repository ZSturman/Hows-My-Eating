# src/utils/detection.py

import cv2
import numpy as np
import mediapipe as mp

class HandDetector:
    """
    Wrapper around Mediapipe Hands. 
    """
    def __init__(self, static_image_mode=False, max_num_hands=2, min_det_conf=0.5):
        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_det_conf
        )

    def detect_hand(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb_frame)
        if result.multi_hand_landmarks:
            return list(result.multi_hand_landmarks)
        return []

def get_hand_hull(hand_landmarks, frame):
    """ Return convex hull points (list of x,y) for the first hand. """
    frame_height, frame_width = frame.shape[:2]
    hand_points = [
        (int(lm.x * frame_width), int(lm.y * frame_height))
        for lm in hand_landmarks.landmark
    ]
    points_array = np.array(hand_points, dtype=np.int32)
    if len(points_array) == 0:
        return []
    hull = cv2.convexHull(points_array)
    hull_points = hull.squeeze().tolist() if len(hull) > 0 else []
    return hull_points

def is_mouth_behind_hand(mouth_points, hand_hull_points):
    """
    Returns True if any mouth point is inside the polygon formed by hand_hull_points.
    """
    if not hand_hull_points:
        return False

    contour = np.array(hand_hull_points, dtype=np.int32).reshape((-1, 1, 2))
    for (x, y) in mouth_points:
        inside = cv2.pointPolygonTest(contour, (float(x), float(y)), False)
        if inside >= 0:
            return True
    return False
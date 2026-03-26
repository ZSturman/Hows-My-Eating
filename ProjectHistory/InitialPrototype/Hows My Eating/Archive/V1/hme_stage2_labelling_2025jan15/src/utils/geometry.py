# src/utils/geometry.py

import numpy as np

def euclidean_distance(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

def compute_mouth_open_ratio(shape_np):
    """
    A simple measure of mouth openness:
    ratio = vertical_distance / horizontal_distance

    Where:
      - vertical distance might be between landmarks 63 (top lip center) and 67 (bottom lip center)
      - horizontal distance might be between landmarks 49 (left mouth corner) and 55 (right mouth corner)
      (In Dlib’s 1-based indexing, those are points #64, #68, #50, #56 in 1-based.)
    """
    # Adjust for 0-based indexing in shape_np:
    top_lip_center = shape_np[62]   # point #63 in 1-based
    bottom_lip_center = shape_np[66] # point #67 in 1-based
    left_corner = shape_np[48]       # point #49 in 1-based
    right_corner = shape_np[54]      # point #55 in 1-based

    vertical_dist = euclidean_distance(top_lip_center, bottom_lip_center)
    horizontal_dist = euclidean_distance(left_corner, right_corner)

    if horizontal_dist == 0:
        return 0.0

    return vertical_dist / horizontal_dist

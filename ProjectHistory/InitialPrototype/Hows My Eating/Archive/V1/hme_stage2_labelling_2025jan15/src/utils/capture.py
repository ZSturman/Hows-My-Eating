# src/utils/capture.py

import cv2

def open_video(video_path: str):
    """
    Opens a video for reading and returns the capture object.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video {video_path}")
    return cap

def create_video_writer(output_path: str, fps: float, width: int, height: int):
    """
    Creates and returns a cv2.VideoWriter for MP4.
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    return out
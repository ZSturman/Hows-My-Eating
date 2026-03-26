"""
Mouth shape extraction: Extract mouth shape parameters from video using MediaPipe.

Processes .mov files frame-by-frame to compute 4 continuous mouth shape
parameters from face landmarks:
  1. mouth_openness  — vertical lip gap normalized by face height
  2. mouth_width     — lip corner distance normalized by face width
  3. jaw_displacement — chin-to-nose distance change from baseline
  4. lip_compression  — inner lip height / outer lip height ratio

These parameters serve as regression labels for training ChewNet
to predict mouth state from AirPods motion data alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pandas as pd

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


# MediaPipe Face Mesh landmark indices for mouth/jaw
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
_UPPER_LIP_TOP = 13       # Top of upper lip (inner)
_LOWER_LIP_BOTTOM = 14    # Bottom of lower lip (inner)
_LEFT_LIP_CORNER = 61     # Left mouth corner
_RIGHT_LIP_CORNER = 291   # Right mouth corner
_CHIN = 152               # Bottom of chin
_NOSE_TIP = 1             # Tip of nose
_FOREHEAD = 10            # Top of forehead (for face height)
_LEFT_EAR = 234           # Left ear tragion (for face width)
_RIGHT_EAR = 454          # Right ear tragion (for face width)

# Inner lip landmarks for compression ratio
_UPPER_LIP_INNER_TOP = 13
_UPPER_LIP_INNER_BOTTOM = 14
_UPPER_LIP_OUTER_TOP = 0     # Center of upper lip outer edge
_LOWER_LIP_OUTER_BOTTOM = 17 # Center of lower lip outer edge


@dataclass
class MouthShapeFrame:
    """Mouth shape parameters for a single video frame."""
    frame_idx: int
    timestamp_sec: float
    mouth_openness: float
    mouth_width: float
    jaw_displacement: float
    lip_compression: float


def _landmark_dist(landmarks, idx_a: int, idx_b: int) -> float:
    """Euclidean distance between two landmarks in normalized coordinates."""
    a = landmarks[idx_a]
    b = landmarks[idx_b]
    return float(np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2))


def _compute_mouth_params(landmarks) -> tuple[float, float, float, float]:
    """
    Compute 4 mouth shape parameters from MediaPipe face landmarks.

    All values are normalized by face dimensions to be scale-invariant.

    Returns:
        (mouth_openness, mouth_width, jaw_displacement, lip_compression)
    """
    # Face reference distances for normalization
    face_height = _landmark_dist(landmarks, _FOREHEAD, _CHIN)
    face_width = _landmark_dist(landmarks, _LEFT_EAR, _RIGHT_EAR)

    if face_height < 1e-6 or face_width < 1e-6:
        return (0.0, 0.0, 0.0, 0.0)

    # 1. Mouth openness: vertical gap between inner lips / face height
    lip_gap = _landmark_dist(landmarks, _UPPER_LIP_TOP, _LOWER_LIP_BOTTOM)
    mouth_openness = lip_gap / face_height

    # 2. Mouth width: horizontal lip corner distance / face width
    lip_width = _landmark_dist(landmarks, _LEFT_LIP_CORNER, _RIGHT_LIP_CORNER)
    mouth_width = lip_width / face_width

    # 3. Jaw displacement: chin-to-nose distance / face height
    #    Higher values = jaw dropped more
    chin_nose = _landmark_dist(landmarks, _CHIN, _NOSE_TIP)
    jaw_displacement = chin_nose / face_height

    # 4. Lip compression: inner lip vertical span / outer lip vertical span
    #    Low values = lips pressed tightly together
    inner_lip_height = _landmark_dist(landmarks, _UPPER_LIP_INNER_TOP, _UPPER_LIP_INNER_BOTTOM)
    outer_lip_height = _landmark_dist(landmarks, _UPPER_LIP_OUTER_TOP, _LOWER_LIP_OUTER_BOTTOM)

    if outer_lip_height < 1e-6:
        lip_compression = 0.0
    else:
        lip_compression = inner_lip_height / outer_lip_height

    return (mouth_openness, mouth_width, jaw_displacement, lip_compression)


MOUTH_SHAPE_COLUMNS = [
    "mouth_openness",
    "mouth_width",
    "jaw_displacement",
    "lip_compression",
]


def extract_mouth_shape_from_video(
    video_path: Path,
    max_faces: int = 1,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
) -> list[MouthShapeFrame]:
    """
    Extract mouth shape parameters from every frame of a video.

    Args:
        video_path: Path to .mov or .mp4 video file
        max_faces: Maximum number of faces to detect (uses first)
        min_detection_confidence: MediaPipe detection confidence threshold
        min_tracking_confidence: MediaPipe tracking confidence threshold

    Returns:
        List of MouthShapeFrame, one per video frame with a detected face.
        Frames where no face is detected are skipped.
    """
    if not MEDIAPIPE_AVAILABLE:
        raise RuntimeError(
            "mediapipe is required for mouth shape extraction.\n"
            "Install with: pip install mediapipe"
        )

    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # Fallback

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=max_faces,
        refine_landmarks=True,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    )

    results: list[MouthShapeFrame] = []
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # MediaPipe expects RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_result = face_mesh.process(rgb)

            if mp_result.multi_face_landmarks:
                landmarks = mp_result.multi_face_landmarks[0].landmark
                openness, width, jaw, compression = _compute_mouth_params(landmarks)

                results.append(MouthShapeFrame(
                    frame_idx=frame_idx,
                    timestamp_sec=frame_idx / fps,
                    mouth_openness=openness,
                    mouth_width=width,
                    jaw_displacement=jaw,
                    lip_compression=compression,
                ))

            frame_idx += 1
    finally:
        cap.release()
        face_mesh.close()

    print(f"  Extracted {len(results)} / {frame_idx} frames with face detected")
    return results


def mouth_shape_to_dataframe(frames: list[MouthShapeFrame]) -> pd.DataFrame:
    """Convert list of MouthShapeFrame to a DataFrame."""
    return pd.DataFrame([
        {
            "frame_idx": f.frame_idx,
            "timestamp_sec": f.timestamp_sec,
            "mouth_openness": f.mouth_openness,
            "mouth_width": f.mouth_width,
            "jaw_displacement": f.jaw_displacement,
            "lip_compression": f.lip_compression,
        }
        for f in frames
    ])


def extract_and_save(
    video_path: Path,
    output_csv: Path,
    **kwargs,
) -> Path:
    """
    Extract mouth shape from video and save to CSV.

    Args:
        video_path: Path to video file
        output_csv: Path for output CSV
        **kwargs: Passed to extract_mouth_shape_from_video

    Returns:
        Path to the saved CSV
    """
    print(f"Extracting mouth shape: {video_path.name}")
    frames = extract_mouth_shape_from_video(video_path, **kwargs)

    if not frames:
        raise ValueError(f"No faces detected in video: {video_path}")

    df = mouth_shape_to_dataframe(frames)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"  Saved: {output_csv} ({len(df)} rows)")
    return output_csv

import datetime
import csv
import os
import cv2
import numpy as np
from imutils import face_utils
from typing import Dict, Optional, Tuple, Union

from config.global_config import get_dlib_detector, get_dlib_predictor
from utils.capture import open_video, create_video_writer
from utils.detection import HandDetector, get_hand_hull, is_mouth_behind_hand
from utils.geometry import euclidean_distance, compute_mouth_open_ratio
from utils.files import get_mov_from_dir

def run_detection_and_calculations(
    video_path: str, output_csv_path: str, logger, output_video_path: Optional[str] = None
) -> Optional[str]:
    """
    Processes a video to detect faces, hands, and mouth features,
    and logs measurements in a CSV file. Optionally, saves the processed frames in a new video.

    Args:
        video_path (str): Path to the input video file.
        output_csv_path (str): Path where the CSV file will be saved.
        logger: Logger instance.
        output_video_path (Optional[str]): Path where the processed video will be saved if provided.

    Returns:
        Optional[str]: Path to the output CSV file, or None if an error occurs.
    """
        
    try:
        logger.info(f"Processing CSV for video: {video_path}")

        # Initialize Dlib and hand detector
        detector = get_dlib_detector()
        predictor = get_dlib_predictor()
        hand_detector = HandDetector()

        # Open video
        cap = open_video(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = None
        if output_video_path:
            out = create_video_writer(output_video_path, fps, frame_width, frame_height)


        # Open CSV
        with open(output_csv_path, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)

            # Build columns
            cols = ['frame', 'timestamp', 'behind_hand', 'mouth_open_ratio']
            left_side_anchor = 49
            left_side_points = [51, 59, 62, 68, 52, 63, 67, 58, 9, 34]
            left_side_lines = [(left_side_anchor, point) for point in left_side_points]

            right_side_anchor = 55
            right_side_points = [53, 57, 64, 66, 52, 63, 67, 58, 9, 34]
            right_side_lines = [(right_side_anchor, point) for point in right_side_points]

            center_connections = [(34, 52), (52, 63), (63, 67), (67, 58), (58, 9)]
            all_pairs = (
                left_side_lines
                + right_side_lines
                + [(left_side_anchor, right_side_anchor)]
                + center_connections
            )

            for i in range(len(all_pairs)):
                cols.append(f'p{all_pairs[i][0]}_p{all_pairs[i][1]}')

            csv_writer.writerow(cols)

            frame_number = 0
            

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    rects = detector(gray, 0)
                    
                    if len(rects) > 1:
                        logger.debug(f"Frame {frame_number}: Detected {len(rects)} faces")
                        
                    if frame_number % 100 == 0:
                        logger.debug(f"Processing frame {frame_number}")

                    # Hand detection
                    hands_detected = hand_detector.detect_hand(frame)

                    # Initialize hand hull
                    first_hand_hull = []  # Default to empty list

                    if hands_detected:
                        first_hand_hull = get_hand_hull(hands_detected[0], frame)
                        if output_video_path:
                            # Draw the detected hand hull
                            cv2.polylines(frame, [np.array(first_hand_hull, np.int32)], True, (0, 255, 255), 2)

                    # Build row
                    row_data = [frame_number, frame_number / fps]
                    behind_hand = False
                    mouth_open = None

                    if len(rects) > 0:
                        for rect in rects:
                            shape = predictor(gray, rect)
                            shape_np = face_utils.shape_to_np(shape)

                            # Mouth points (48:68 => 0-based 48..67)
                            mouth_points = shape_np[48:68]

                            # Check if mouth is behind hand
                            if first_hand_hull:
                                behind_hand = is_mouth_behind_hand(mouth_points, first_hand_hull)

                            # Compute mouth open ratio
                            mouth_open = compute_mouth_open_ratio(shape_np)

                            # Draw mouth points and lines
                            for iA, jA in all_pairs:
                                ptA = shape_np[iA - 1]
                                ptB = shape_np[jA - 1]
                                distance = euclidean_distance(ptA, ptB)
                                row_data.append(distance)
                                
                                if output_video_path:
                                    cv2.circle(frame, tuple(ptA), 3, (0, 0, 255), -1)
                                    cv2.circle(frame, tuple(ptB), 3, (0, 0, 255), -1)
                                    cv2.line(frame, tuple(ptA), tuple(ptB), (0, 255, 0), 1)

                            break  # Process only the first detected face

                    else:
                        # No face detected => fill None
                        row_data.extend([None] * len(all_pairs))

                    # Insert behind_hand and mouth_open
                    row_data.insert(2, behind_hand)
                    row_data.insert(3, mouth_open)

                    # Write row to CSV
                    csv_writer.writerow(row_data)

                    if output_video_path:
                        # Write frame to video
                        out.write(frame)

                    frame_number += 1

            finally:
                cap.release()
                if output_video_path:
                    out.release()

        logger.info(f"Processing completed. CSV data saved to {output_csv_path}")
        if output_video_path:
            logger.info(f"Processed video saved to {output_video_path}")
            return output_csv_path, output_video_path
        return output_csv_path
    except Exception as e:
        logger.error(f"An error occurred during the processing of the video: {e}", exc_info=True)
        return None
    

def process_visuals(collected_data_path: str, processed_visuals_file_name: str, output_video: bool, logger) -> Union[Dict[str, Optional[Union[Dict, str]]], str]:
    """
    Handles the video processing pipeline, extracting and analyzing data from a .mov file.

    Args:
        collected_data_path (str): Path to the directory containing the video.
        output_video (bool): Whether to generate a processed output video.
        logger: Logger instance.

    Returns:
        Union[Dict[str, Optional[Union[Dict, str]]], str]:
            A dictionary containing processed data and file paths, or an error message.
    """
    try:
        video_path = get_mov_from_dir(collected_data_path)
        if not video_path:
            raise FileNotFoundError(
                f"No matching .mov file found in '{collected_data_path}'. Ensure the file name matches the directory name."
            )

        output_csv_path = os.path.join(collected_data_path, f"{processed_visuals_file_name}.csv")

        output_video_path = os.path.join(collected_data_path, f"{processed_visuals_file_name}.mp4") if output_video else None
        result_file = run_detection_and_calculations(video_path, output_csv_path, logger, output_video_path)
        
        if result_file:
            return {"csv_file": output_csv_path, "video_file": output_video_path} if output_video else {"csv_file": output_csv_path}
    except Exception as e:
        logger.error(f"An error occurred during the processing: {e}", exc_info=True)
        return f"An error occurred during the processing: {e}"
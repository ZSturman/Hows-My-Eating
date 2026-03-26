# step1.py
# Description: This script reads a video file, detects faces in each frame, and calculates the distance between facial landmarks.
import cv2
import dlib
import numpy as np
import csv
from imutils import face_utils
import mediapipe as mp

# Load the pre-trained facial landmark predictor from dlib
predictor_path = "landmarks_models/shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

def detect_hand(frame):
    hands_detected = []
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            hands_detected.append(hand_landmarks)
    
    return hands_detected

def get_hand_hull(hand_landmarks, frame_size):
    frame_height, frame_width = frame_size[:2]
    hand_points = [(int(lm.x * frame_width), int(lm.y * frame_height)) for lm in hand_landmarks.landmark]
    points_array = np.array(hand_points, np.int32)
    
    if len(points_array) > 0:
        hull = cv2.convexHull(points_array)
        hull_points = hull.squeeze().tolist() if len(hull) > 0 else []
    else:
        hull_points = []
    
    return hull_points

def is_mouth_behind_hand(mouth_points, hand_hull_points):
    hand_hull_contour = np.array(hand_hull_points, dtype=np.int32).reshape((-1, 1, 2))
    for point in mouth_points:
        x, y = float(point[0]), float(point[1])
        inside = cv2.pointPolygonTest(hand_hull_contour, (x, y), False)
        if inside >= 0:
            return True
    return False

# Function to calculate the distance between two points
def euclidean_distance(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

# Initialize the video capture
video_path = 'new_video.mov'  # Update the path to your video file
cap = cv2.VideoCapture(video_path)

# Get the frames per second (FPS) of the video
fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Initialize video writer to save the processed frames
output_video_path = 'step1.mp4'  # Path to save the processed video
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for mp4
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

# Open a CSV file to write the data
csv_file = open('step1.csv', mode='w', newline='')
csv_writer = csv.writer(csv_file)

# Write the CSV header
cols = ['frame', 'timestamp', 'behind_hand']

left_side_anchor = 49
left_side_points = [51, 59, 62, 68, 52, 63, 67, 58, 9, 34]
left_side_lines = [(left_side_anchor, point) for point in left_side_points]

right_side_anchor = 55
right_side_points = [53, 57, 64, 66, 52, 63, 67, 58, 9, 34]
right_side_lines = [(right_side_anchor, point) for point in right_side_points]

center_connections = [(34, 52), (52, 63), (63, 67), (67, 58), (58, 9)]

all_pairs = left_side_lines + right_side_lines + [(left_side_anchor, right_side_anchor)] + center_connections

for i in range(1, len(all_pairs) + 1):
    cols.append(f'p{all_pairs[i-1][0]}_p{all_pairs[i-1][1]}')

csv_writer.writerow(cols)
frame_number = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)
        hands_detected = detect_hand(frame)

        # Initialize the row data with frame number and timestamp
        row = [frame_number, frame_number / fps]

        # Initialize behindHand variable
        behindHand = False

        # Only process if faces are detected
        if rects:
            for rect in rects:
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
                
                mouth_points = shape[48:68]  # Note: 49-68 in 1-index is 48-67 in 0-index

                hand_hull_points = []
                if hands_detected:
                    # Record the convex hull of the detected hand
                    hand_hull_points = get_hand_hull(hands_detected[0], frame.shape)

                # Determine if any mouth points are behind the hand
                if len(hand_hull_points) > 0:
                    behindHand = is_mouth_behind_hand(mouth_points, hand_hull_points)
                    cv2.polylines(frame, [np.array(hand_hull_points, np.int32)], True, (0, 255, 255), 2)

                # Calculate distances and draw on the frame
                for (i, j) in all_pairs:
                    ptA = shape[i-1]
                    ptB = shape[j-1]
                    distance = euclidean_distance(ptA, ptB)
                    row.append(distance)

                    # Draw the points
                    cv2.circle(frame, tuple(ptA), 3, (0, 0, 255), -1)
                    cv2.circle(frame, tuple(ptB), 3, (0, 0, 255), -1)

                    # Draw the line between the points
                    cv2.line(frame, tuple(ptA), tuple(ptB), (0, 255, 0), 1)
                    

        else:
            # If no face is detected, append None for each distance
            row.extend([None] * len(all_pairs))

        # Append the behindHand value to the row
        row.insert(2, behindHand)

        # Overlay the behindHand value on the frame
        text = f"Behind Hand: {behindHand}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Write the row to the CSV file
        csv_writer.writerow(row)

        # Write the frame to the output video
        out.write(frame)

        # Display the frame
        cv2.imshow("Frame", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
            break

        # Increment the frame number
        frame_number += 1

finally:
    # Release resources
    cap.release()
    out.release()
    csv_file.close()
    cv2.destroyAllWindows()
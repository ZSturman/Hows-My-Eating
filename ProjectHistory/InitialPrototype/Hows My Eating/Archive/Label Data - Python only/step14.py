import cv2
import dlib
import numpy as np
import joblib
import pandas as pd
import warnings
from imutils import face_utils
import mediapipe as mp

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=UserWarning, message="SymbolDatabase.GetPrototype() is deprecated")

# Load the classifiers
clf_teeth = joblib.load('clf_teeth.pkl')
clf_lips = joblib.load('clf_lips.pkl')
clf_action = joblib.load('clf_action.pkl')

# Load the label encoders
le_teeth = joblib.load('le_teeth.pkl')
le_lips = joblib.load('le_lips.pkl')
le_action = joblib.load('le_action.pkl')

# Load the saved feature order
feature_order = joblib.load('feature_order.pkl')

# Load dlib's face detector and shape predictor
predictor_path = "landmarks_models/shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

# Initialize MediaPipe Hands
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

def extract_features_from_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    hands_detected = detect_hand(frame)

    features = []

    left_side_anchor = 49
    left_side_points = [51, 59, 62, 68, 52, 63, 67, 58, 9, 34]
    left_side_lines = [(left_side_anchor, point) for point in left_side_points]

    right_side_anchor = 55
    right_side_points = [53, 57, 64, 66, 52, 63, 67, 58, 9, 34]
    right_side_lines = [(right_side_anchor, point) for point in right_side_points]

    center_connections = [(34, 52), (52, 63), (63, 67), (67, 58), (58, 9)]

    all_pairs = left_side_lines + right_side_lines + [(left_side_anchor, right_side_anchor)] + center_connections

    behindHand = False
    if rects:
        for rect in rects:
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)
            mouth_points = shape[48:68]

            hand_hull_points = []
            if hands_detected:
                hand_hull_points = get_hand_hull(hands_detected[0], frame.shape)
            
            if len(hand_hull_points) > 0:
                behindHand = is_mouth_behind_hand(mouth_points, hand_hull_points)

            for (i, j) in all_pairs:
                ptA = shape[i-1]
                ptB = shape[j-1]
                distance = np.linalg.norm(ptA - ptB)
                features.append(distance)
    
    # If no face is detected, append zeros (or a fallback value) for each distance
    if not features:
        features = [0] * len(all_pairs)
    
    # Add the behindHand feature if it was used during training
    features.append(1 if behindHand else 0)

    # Convert to DataFrame and ensure the features are in the correct order
    features_df = pd.DataFrame([features], columns=feature_order)
    
    return features_df

# Load your new video
video_path = 'new_video.mov'
cap = cv2.VideoCapture(video_path)

# Prepare for saving the new video with overlaid predictions
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output_video_with_predictions.avi', fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))

# Prepare a list to collect data for the new CSV
output_data = []
frame_number = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Extract features from the current frame
    features_df = extract_features_from_frame(frame)

    # Predict the labels using the trained models
    teeth_prediction = clf_teeth.predict(features_df)[0]
    lips_prediction = clf_lips.predict(features_df)[0]
    action_prediction = clf_action.predict(features_df)[0]

    # Convert predictions back to their original labels
    teeth_label = le_teeth.inverse_transform([teeth_prediction])[0]
    lips_label = le_lips.inverse_transform([lips_prediction])[0]
    action_label = le_action.inverse_transform([action_prediction])[0]

    # Overlay the predictions on the video frame
    cv2.putText(frame, f'Teeth: {teeth_label}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, f'Lips: {lips_label}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(frame, f'Action: {action_label}', (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

    # Display the frame with the overlay in a window
    cv2.imshow('Frame with Predictions', frame)

    # Save the frame with the overlay to the new video
    out.write(frame)

    # Add the prediction data to the output list
    output_data.append([frame_number, cap.get(cv2.CAP_PROP_POS_MSEC), teeth_label, lips_label, action_label])

    frame_number += 1

    # Break the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video resources
cap.release()
out.release()

# Close all OpenCV windows
cv2.destroyAllWindows()

# Create a DataFrame for the new CSV
output_df = pd.DataFrame(output_data, columns=['frame', 'timestamp', 'teeth', 'lips', 'action'])

# Save the new CSV file
output_df.to_csv('generated_labels.csv', index=False)

print('New video with predictions and CSV generated successfully.')

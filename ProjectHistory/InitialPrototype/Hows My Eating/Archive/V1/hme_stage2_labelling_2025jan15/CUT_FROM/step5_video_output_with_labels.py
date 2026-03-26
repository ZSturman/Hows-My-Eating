# step5.py
import cv2
import pandas as pd

# Load the video
video_path = 'data/video.mov'
cap = cv2.VideoCapture(video_path)

# Load the CSV file
csv_path = 'step4.csv'
df = pd.read_csv(csv_path)

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Output video settings
output_path = 'step5.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

frame_number = 0

while(cap.isOpened()):
    ret, frame = cap.read()
    if not ret:
        break
    
    if frame_number < len(df):
        # Get the data from the corresponding frame in the CSV
        row = df.iloc[frame_number]
        chew_count = row['chew_count']
        teeth = row['teeth']
        lips = row['lips']
        action = row['action']
        
        # Overlay the text on the video frame
        text = f'Chew Count: {chew_count}, Teeth: {teeth}, Lips: {lips}, Action: {action}'
        cv2.putText(frame, text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
    # Write the frame with the overlay text to the output video
    out.write(frame)
    
    frame_number += 1

    if frame_number >= total_frames:
        break

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()
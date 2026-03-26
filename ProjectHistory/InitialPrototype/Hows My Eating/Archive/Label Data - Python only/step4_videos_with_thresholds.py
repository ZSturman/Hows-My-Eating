# step4.py
# Description: This script reads the CSV files generated in step3 and overlays the data on the video frames.
import cv2
import pandas as pd
import os

video_path = 'data/video.mov'  

# Main directory containing the step3 csvs
step3_dir = "step3"

# List all files in step3_dir that end with .csv
csv_files = [f for f in os.listdir(step3_dir) if f.endswith('.csv')]

output_dir = 'step4'
os.makedirs(output_dir, exist_ok=True)

for file in csv_files:
    # Load the CSV file
    data = pd.read_csv(step3_dir + "/" + file)

    # Load data into a pandas DataFrame
    df = pd.DataFrame(data)
    cap = cv2.VideoCapture(video_path)
    
    output_path = f'{output_dir}/{file.split(".")[0]}.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Get the frame width, height, and frames per second
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Create a video writer object
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # Font settings for text overlay
    font = cv2.FONT_HERSHEY_SIMPLEX
    little_font_scale = 1
    big_font_scale = 2
    main_font_color = (0, 255, 255)  # Yellow
    open_font_color = (255, 0, 255)  # Magenta
    closed_font_color = (255, 255, 0)  # Cyan
    little_font_thickness = 2
    big_font_thickness = 4
    line_type = cv2.LINE_AA

    # Iterate over each frame in the video
    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get corresponding row data from dataframe
        if frame_number < len(df):
            row_data = df.iloc[frame_number]
            
            # Prepare the text for each line
            csv_title = file.split(".")[0]
            frame_text = f"Frame: {int(row_data['frame'])}"
            timestamp_text = f"Timestamp: {row_data['timestamp']:.2f}"
            thresh1 = f"Threshold 1: {row_data['thresh_1']}"
            thresh2 = f"Threshold 2: {row_data['thresh_2']}"
            thresh3 = f"Threshold 3: {row_data['thresh_3']}"
            thresh4 = f"Threshold 4: {row_data['thresh_4']}"
            thresh5 = f"Threshold 5: {row_data['thresh_5']}"
        
            # Initial text position
            text_x = 10
            text_y = 50  
            
            thresh1_color = open_font_color if row_data['thresh_1'] == 'Open' else closed_font_color
            thresh2_color = open_font_color if row_data['thresh_2'] == 'Open' else closed_font_color
            thresh3_color = open_font_color if row_data['thresh_3'] == 'Open' else closed_font_color
            thresh4_color = open_font_color if row_data['thresh_4'] == 'Open' else closed_font_color
            thresh5_color = open_font_color if row_data['thresh_5'] == 'Open' else closed_font_color
            
            # Overlay each text line on the frame
            cv2.putText(frame, csv_title, (text_x, text_y), font, little_font_scale, main_font_color, little_font_thickness, line_type)
            cv2.putText(frame, frame_text, (text_x, text_y+35), font, little_font_scale, main_font_color, little_font_thickness, line_type)
            cv2.putText(frame, timestamp_text, (text_x, text_y + 70), font, little_font_scale, main_font_color, little_font_thickness, line_type)
            cv2.putText(frame, thresh1, (text_x, text_y + 140), font, big_font_scale, thresh1_color, big_font_thickness, line_type)
            cv2.putText(frame, thresh2, (text_x, text_y + 210), font, big_font_scale, thresh2_color, big_font_thickness, line_type)
            cv2.putText(frame, thresh3, (text_x, text_y + 280), font, big_font_scale, thresh3_color, big_font_thickness, line_type)
            cv2.putText(frame, thresh4, (text_x, text_y + 350), font, big_font_scale, thresh4_color, big_font_thickness, line_type)
            cv2.putText(frame, thresh5, (text_x, text_y + 420), font, big_font_scale, thresh5_color, big_font_thickness, line_type)
            
            
        
        # Display the frame with the overlay text
        cv2.imshow('Video Frame with Data Overlay', frame)
        
        
        
        # Wait for a brief moment before displaying the next frame
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

        frame_number += 1
        
        # Write the frame to the output video
        out.write(frame)
        

    # Release video capture object and close all OpenCV windows
    cap.release()
    out.release()
    cv2.destroyAllWindows()
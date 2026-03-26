import cv2
import pandas as pd
import os

video_path = 'data/video.mov'

# Main directory containing the step3 csvs
step3_dir = "step3"

# List all files in step3_dir that end with .csv
csv_files = [f for f in os.listdir(step3_dir) if f.endswith('.csv')]

output_dir = 'step7'
os.makedirs(output_dir, exist_ok=True)

manual_labels_csv = 'step6.csv'
manual_labels = pd.read_csv(manual_labels_csv)

# Define colors
open_font_color = (0, 255, 0)  # Green for "Open"
closed_font_color = (0, 0, 255)  # Red for "Closed"
thresh_color = (255, 255, 255)  # White for the threshold text

# Function to render text with different colors
def render_colored_text(frame, text, pos, font, scale, thickness, colors):
    x, y = pos
    for i, word in enumerate(text.split()):
        cv2.putText(frame, word, (x, y), font, scale, colors[i], thickness, line_type)
        text_size = cv2.getTextSize(word, font, scale, thickness)[0]
        x += text_size[0] + 10  # Move to the right for the next word

for file in csv_files:
    # Load the CSV file
    data = pd.read_csv(os.path.join(step3_dir, file))

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
    little_font_scale = 0.6
    big_font_scale = 1.2
    little_font_thickness = 1
    big_font_thickness = 2
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
            manual_data = manual_labels.iloc[frame_number]

            # Prepare the text for each line
            csv_title = file.split(".")[0]
            frame_text = f"Frame: {int(row_data['frame'])}"
            timestamp_text = f"Timestamp: {row_data['timestamp']:.2f}"

            # Prepare text and determine colors for threshold and manual labels
            for i in range(1, 6):
                thresh_value = row_data[f'thresh_{i}'].lower()
                teeth_value = manual_data['teeth'].lower()
                lips_value = manual_data['lips'].lower()

                # Determine color for threshold, teeth, and lips based on "open" or "closed"
                thresh_color_value = open_font_color if thresh_value == 'open' else closed_font_color
                teeth_color_value = open_font_color if teeth_value == 'open' else closed_font_color
                lips_color_value = open_font_color if lips_value == 'open' else closed_font_color

                # Check for match and adjust color accordingly
                thresh_teeth_match = thresh_color_value if thresh_value == teeth_value else closed_font_color
                thresh_lips_match = thresh_color_value if thresh_value == lips_value else closed_font_color

                # Text for each threshold
                thresh_text = f"{i}: {row_data[f'thresh_{i}']} | T:{manual_data['teeth']} L:{manual_data['lips']}"
                colors = [thresh_color, thresh_teeth_match, thresh_color, teeth_color_value, thresh_color, lips_color_value]

                # Overlay each text line on the frame
                render_colored_text(frame, thresh_text, (10, 200 + (i-1)*60), font, big_font_scale, big_font_thickness, colors)

            # Overlay title and frame/timestamp info
            cv2.putText(frame, csv_title, (10, 50), font, little_font_scale, thresh_color, little_font_thickness, line_type)
            cv2.putText(frame, frame_text, (10, 75), font, little_font_scale, thresh_color, little_font_thickness, line_type)
            cv2.putText(frame, timestamp_text, (10, 100), font, little_font_scale, thresh_color, little_font_thickness, line_type)

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

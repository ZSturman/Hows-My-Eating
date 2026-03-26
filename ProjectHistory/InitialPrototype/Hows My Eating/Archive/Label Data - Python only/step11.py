import os
import pandas as pd
import numpy as np
import cv2

def read_labels_from_step10(step10_dir):
    # Read all CSV files from step10 directory
    csv_files = [f for f in os.listdir(step10_dir) if f.endswith('.csv')]
    label_data = {}
    for csv_file in csv_files:
        feature_name = csv_file.replace('_labels.csv', '')
        df = pd.read_csv(os.path.join(step10_dir, csv_file))
        label_data[feature_name] = df[['frame', 'teeth_label', 'lips_label']]
        
    return label_data

def calculate_accuracies(label_data, manual_labels):
    accuracies = {}
    for feature, df in label_data.items():
        merged_df = pd.merge(df, manual_labels[['frame', 'teeth', 'lips']], on='frame', how='left')
        teeth_correct = (merged_df['teeth_label'].str.lower() == merged_df['teeth'].str.lower()).mean()
        lips_correct = (merged_df['lips_label'].str.lower() == merged_df['lips'].str.lower()).mean()
        accuracies[feature] = {'teeth_accuracy': teeth_correct, 'lips_accuracy': lips_correct}
    return accuracies

def combine_labels_with_weights(label_data, teeth_weights, lips_weights):
    features = list(label_data.keys())
    frames = label_data[features[0]]['frame']
    combined_labels = pd.DataFrame({'frame': frames})

    teeth_votes = np.zeros(len(frames))
    lips_votes = np.zeros(len(frames))

    for feature in features:
        teeth_labels = label_data[feature]['teeth_label'].str.lower().replace({'open': 1, 'closed': 0}).to_numpy()
        lips_labels = label_data[feature]['lips_label'].str.lower().replace({'open': 1, 'closed': 0}).to_numpy()

        teeth_votes += teeth_weights[feature] * teeth_labels
        lips_votes += lips_weights[feature] * lips_labels

    # Convert votes to labels based on the weighted sum
    combined_labels['teeth_label'] = np.where(teeth_votes >= 0.5, 'Open', 'Closed')
    combined_labels['lips_label'] = np.where(lips_votes >= 0.5, 'Open', 'Closed')

    return combined_labels

def compare_with_manual_labels(combined_labels, manual_labels):
    # Merge combined labels with manual labels on 'frame'
    merged_df = pd.merge(combined_labels, manual_labels[['frame', 'teeth', 'lips']], on='frame', how='left')
    # Create columns indicating agreement
    merged_df['teeth_agree'] = merged_df['teeth_label'].str.lower() == merged_df['teeth'].str.lower()
    merged_df['lips_agree'] = merged_df['lips_label'].str.lower() == merged_df['lips'].str.lower()
    return merged_df

def normalize_accuracies(accuracies):
    # Extract accuracies for teeth and lips
    teeth_accuracies = {k: v['teeth_accuracy'] for k, v in accuracies.items()}
    lips_accuracies = {k: v['lips_accuracy'] for k, v in accuracies.items()}
    
    # Calculate the total sum of accuracies
    total_teeth_accuracy = sum(teeth_accuracies.values())
    total_lips_accuracy = sum(lips_accuracies.values())
    
    # Normalize to generate weights
    teeth_weights = {k: v / total_teeth_accuracy for k, v in teeth_accuracies.items()}
    lips_weights = {k: v / total_lips_accuracy for k, v in lips_accuracies.items()}
    
    return teeth_weights, lips_weights

def overlay_labels_on_video(feature_name, feature_labels, manual_labels, video_path, output_dir):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_path = os.path.join(output_dir, f'{feature_name}_output.mp4')
    
    # Create a video writer object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # Font settings for text overlay
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    font_thickness = 3
    line_type = cv2.LINE_AA

    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number < len(feature_labels):
            row = feature_labels.iloc[frame_number]
            manual_row = manual_labels.iloc[frame_number]

            # Prepare the text to overlay
            teeth_text = f"Teeth: {row['teeth_label']}"
            lips_text = f"Lips: {row['lips_label']}"

            # Set the color based on agreement with manual labels
            teeth_color = (0, 255, 0) if row['teeth_label'].lower() == manual_row['teeth'].lower() else (0, 0, 255)
            lips_color = (0, 255, 0) if row['lips_label'].lower() == manual_row['lips'].lower() else (0, 0, 255)

            # Positions for the text
            text_x = 50
            text_y_teeth = 100
            text_y_lips = 200

            # Overlay the text on the frame
            cv2.putText(frame, teeth_text, (text_x, text_y_teeth), font, font_scale, teeth_color, font_thickness, line_type)
            cv2.putText(frame, lips_text, (text_x, text_y_lips), font, font_scale, lips_color, font_thickness, line_type)

        # Write the frame to the output video
        out.write(frame)

        # Display the frame in a window
        cv2.imshow(f'{feature_name} Video Frame', frame)

        # Wait for a brief moment before displaying the next frame
        if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
            break

        frame_number += 1

    cap.release()
    out.release()
    cv2.destroyAllWindows()

def main():
    # Paths
    step10_dir = 'step10'
    manual_labels_csv = 'step6.csv'
    video_path = 'data/video.mov'  # Update if needed
    output_dir = 'output_videos'
    os.makedirs(output_dir, exist_ok=True)

    # Read labels from step10
    label_data = read_labels_from_step10(step10_dir)

    # Read manual labels
    manual_labels = pd.read_csv(manual_labels_csv)

    # Calculate accuracies
    accuracies = calculate_accuracies(label_data, manual_labels)

    # Generate weights based on accuracies
    teeth_weights, lips_weights = normalize_accuracies(accuracies)

    # Create and save a video for each feature
    for feature_name, feature_labels in label_data.items():
        overlay_labels_on_video(feature_name, feature_labels, manual_labels, video_path, output_dir)

    # Combine labels using weighted voting
    combined_labels = combine_labels_with_weights(label_data, teeth_weights, lips_weights)

    # Compare with manual labels
    merged_df = compare_with_manual_labels(combined_labels, manual_labels)

    # Save combined output video
    overlay_labels_on_video('combined', merged_df, manual_labels, video_path, output_dir)

    print(f"Output videos saved to {output_dir}")

if __name__ == "__main__":
    main()

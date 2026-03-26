# step10.py
# Description: This script reads 'step9_thresholds.json' and generates labels using the best thresholds for 'lips' and 'teeth'.

import pandas as pd
import json
import os

def generate_labels(column_data, threshold_value, flipped):
    labels = []
    for value in column_data:
        if flipped:
            if value > threshold_value:
                labels.append('Closed')
            else:
                labels.append('Open')
        else:
            if value < threshold_value:
                labels.append('Closed')
            else:
                labels.append('Open')
    return labels

def process_csv(input_csv, thresholds_json):
    # Create 'step10' directory if it doesn't exist
    output_dir = 'step10'
    os.makedirs(output_dir, exist_ok=True)

    # Load 'step2.csv'
    df = pd.read_csv(input_csv)

    # Extract 'frame' and 'timestamp' columns
    frame = df['frame']
    timestamp = df['timestamp']

    # Iterate over each feature
    for feature_name, threshold_info in thresholds_json.items():
        # Check if the feature exists in the dataframe
        if feature_name not in df.columns:
            print(f"Feature '{feature_name}' not found in the data. Skipping.")
            continue

        column_data = df[feature_name]

        # For 'lips' and 'teeth', generate labels
        labels = {}
        for label_type in ['lips', 'teeth']:
            threshold_label = threshold_info[label_type]['threshold']
            # Convert 'thresh_1' to the actual threshold value
            # We'll need to read the thresholds from the original 'step3' JSON files
            # Let's read the thresholds from 'step3/{feature_name}_thresholds.json'

            threshold_json_path = f'step3/{feature_name}_thresholds.json'
            if not os.path.exists(threshold_json_path):
                print(f"Threshold JSON file '{threshold_json_path}' not found. Skipping.")
                continue

            with open(threshold_json_path, 'r') as f:
                threshold_data = json.load(f)
            # Get the threshold values
            thresholds = threshold_data['thresholds']
            # Map 'thresh_1' to the corresponding threshold value
            thresh_index = int(threshold_label.split('_')[1]) - 1  # 'thresh_1' -> index 0
            threshold_value = thresholds[thresh_index]
            flipped = threshold_info[label_type]['flipped']

            # Generate labels
            labels[label_type] = generate_labels(column_data, threshold_value, flipped)

        # Create a new DataFrame for this feature
        new_df = pd.DataFrame({
            'frame': frame,
            'timestamp': timestamp,
            feature_name: column_data,
            'lips_label': labels['lips'],
            'teeth_label': labels['teeth']
        })

        # Define the output CSV file path
        csv_filename = os.path.join(output_dir, f'{feature_name}_labels.csv')

        # Save the DataFrame to a CSV file
        new_df.to_csv(csv_filename, index=False)

        print(f"Labels for feature '{feature_name}' saved to '{csv_filename}'.")

# Read 'step9_thresholds.json'
with open('step9.json', 'r') as f:
    thresholds_json = json.load(f)

input_csv = 'step2.csv'
process_csv(input_csv, thresholds_json)

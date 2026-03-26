# step3.py
# Description: This script reads the CSV file generated in step2.py and generates new CSV files and JSON files for each column.
import pandas as pd
import numpy as np
import os
import json

def generate_threshold_labels(column_data, thresholds):
    labels = []
    for value in column_data:
        label_row = []
        for threshold in thresholds:
            if value < threshold:
                label_row.append('Closed')
            else:
                label_row.append('Open')
        labels.append(label_row)
    return np.array(labels)

def process_csv(input_csv, num_thresholds=5):
    # Create 'step3' directory if it doesn't exist
    output_dir = 'step3'
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the CSV
    df = pd.read_csv(input_csv)

    # Extract 'frame' and 'timestamp' columns
    frame = df.pop('frame')
    timestamp = df.pop('timestamp')

    # Iterate over each column to generate new CSV files and JSON files
    for column in df.columns:
        column_data = df[column]
        min_val, max_val = column_data.min(), column_data.max()

        # Calculate thresholds (equidistant between min and max)
        thresholds = np.linspace(min_val, max_val, num=num_thresholds+2)[1:-1]

        # Generate labels based on thresholds
        threshold_labels = generate_threshold_labels(column_data, thresholds)

        # Create a new DataFrame for this column
        new_df = pd.DataFrame({
            'frame': frame,
            'timestamp': timestamp,
            column: column_data
        })

        # Add columns for each threshold label
        for i, threshold in enumerate(thresholds):
            new_df[f'thresh_{i+1}'] = threshold_labels[:, i]

        # Define the file paths
        csv_filename = os.path.join(output_dir, f'{column}_thresholds.csv')
        json_filename = os.path.join(output_dir, f'{column}_thresholds.json')

        # Save the new DataFrame to a CSV file
        new_df.to_csv(csv_filename, index=False)

        # Save the thresholds info to a JSON file
        thresholds_info = {
            'min': float(min_val),
            'max': float(max_val),
            'thresholds': thresholds.tolist()
        }
        with open(json_filename, 'w') as json_file:
            json.dump(thresholds_info, json_file, indent=4)


input_csv = 'step2.csv'
process_csv(input_csv)
import csv
import json
import sys
import os
from collections import defaultdict
import pandas as pd


def extract_timestamps(csv_file_path):
    """Extract start and end timestamps for each bite count."""
    timestamps = defaultdict(lambda: {"start": float('inf'), "end": float('-inf')})
    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            try:
                bite_count = int(row['bite_count'])
                timestamp = float(row['timestamp'])
                
                if bite_count == 0:
                    continue
                
                timestamps[bite_count]["start"] = min(timestamps[bite_count]["start"], timestamp)
                timestamps[bite_count]["end"] = max(timestamps[bite_count]["end"], timestamp)
            except (ValueError, KeyError):
                continue
    
    # Convert defaultdict to a standard dict for JSON serialization
    return dict(timestamps)


def save_json(data, json_file_path):
    """Save data to a JSON file."""
    with open(json_file_path, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    return json.dumps(data)


def get_folder_name(path):
    """Extract folder name from path."""
    return os.path.basename(path)


def find_csv_files_starting_with(path, prefix="labelled_data"):
    """Find CSV files in a directory that start with the given prefix."""
    return [file for file in os.listdir(path) if file.startswith(prefix)]


def load_motion_data(path, folder_name):
    """Load motion data JSON files."""
    return [file for file in os.listdir(path) if file == f"{folder_name}.json"]


def create_pandas_dataframe(json_file_path):
    """Convert JSON motion data to a Pandas DataFrame."""
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        
    return pd.DataFrame(data)

def preprocess_motion_data(df):
    """Clean and preprocess motion data DataFrame."""
    # Normalize timestamps to start at 0
    df['timestamp'] = df['timestamp'] - df['timestamp'].min()
    return df


def split_and_save_motion_data(motion_df, timestamps, output_path):
    """Split motion data based on JSON timestamps and save to CSV files."""
    for key, time_range in timestamps.items():
        start_time = time_range["start"]
        end_time = time_range["end"]
        
        # Find the rows closest to the start and end times
        subset = motion_df[
            (motion_df['timestamp'] >= start_time) &
            (motion_df['timestamp'] <= end_time)
        ]
        
        # Save the subset to a new CSV file
        output_folder = os.path.join(output_path, "chewing")
        os.makedirs(output_folder, exist_ok=True)
        
        number_of_rows = len(subset)
        
        output_file = os.path.join(output_folder, f"motion_data_{key}_rows_{number_of_rows}.csv")
        subset.to_csv(output_file, index=False)
        print(f"Saved {output_file}")
    

def preprocess_motion_data(df):
    """Clean and preprocess motion data DataFrame."""
    # Normalize timestamps to start at 0
    df['timestamp'] = df['timestamp'] - df['timestamp'].min()
    
    # Remove unnecessary columns
    df = df.drop(columns=['transformedRotation'], errors='ignore')
    
    # Split nested fields into separate columns
    for field in ['userAcceleration', 'gravity', 'rotationRate', 'attitude']:
        if field in df.columns:
            for axis in ['x', 'y', 'z']:
                if axis in df[field][0]:  # Check if axis exists in data
                    df[f'{field}_{axis}'] = df[field].apply(lambda x: x[axis])
            if field == 'attitude':  # Additional processing for 'attitude'
                for angle in ['roll', 'pitch', 'yaw']:
                    df[f'{field}_{angle}'] = df[field].apply(lambda x: x[angle])
            df = df.drop(columns=[field])
    
    return df


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <odir path>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    # Find and process CSV file
    csv_files = find_csv_files_starting_with(path)
    if not csv_files:
        print("No labelled_data CSV files found.")
        sys.exit(1)
    csv_file_path = os.path.join(path, csv_files[0])
    
    timestamps = extract_timestamps(csv_file_path)
    json_file_path = os.path.join(path, "timestamps.json")
    json_timestamps = save_json(timestamps, json_file_path)
    
    # Process motion data
    folder_name = get_folder_name(path)
    motion_data_path = os.path.join(path, "extra")
    motion_data_files = load_motion_data(motion_data_path, folder_name)
    if not motion_data_files:
        print("No motion data JSON files found.")
        sys.exit(1)
    motion_file_path = os.path.join(motion_data_path, motion_data_files[0])
    motion_df = create_pandas_dataframe(motion_file_path)
    motion_df = preprocess_motion_data(motion_df)
    
    # Save motion data to a CSV file
    motion_df.to_csv(os.path.join(path, "motion_data.csv"), index=False)
    
    # Split motion data and save to separate CSV files
    split_and_save_motion_data(motion_df, timestamps, path)


if __name__ == "__main__":
    main()
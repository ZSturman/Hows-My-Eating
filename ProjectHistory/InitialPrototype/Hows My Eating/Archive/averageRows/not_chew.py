import json
import sys
import os
import pandas as pd


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


def split_motion_data_by_length(df, lengths, output_path):
    """Split motion data into subsets of specified lengths and save to CSV files."""
    start_idx = 0
    for i, length in enumerate(lengths):
        end_idx = start_idx + length
        
        # Check if the length exceeds the available data
        if end_idx > len(df):
            print(f"Length {length} for subset {i+1} exceeds available data. Adjusting to end of DataFrame.")
            end_idx = len(df)
        
        subset = df.iloc[start_idx:end_idx]
        start_idx = end_idx
        
        # Save the subset to a CSV file
        output_file = os.path.join(output_path, f"motion_data_subset_{i+1}_rows_{length}.csv")
        subset.to_csv(output_file, index=False)
        print(f"Saved {output_file}")
        
        # Break if there is no more data left to split
        if start_idx >= len(df):
            print("No more data to split.")
            break


def main():
    if len(sys.argv) < 3:
        print("Usage: python split_motion_data_by_length.py <json_file_path> <length1> <length2> ...")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    lengths = list(map(int, sys.argv[2:]))
    output_path = os.path.dirname(json_file_path)
    
    # Load motion data JSON
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Convert JSON data to a Pandas DataFrame
    motion_df = pd.DataFrame(data)
    
    # Preprocess the motion data
    motion_df = preprocess_motion_data(motion_df)
    
    # Split motion data into subsets and save to CSV files
    split_motion_data_by_length(motion_df, lengths, output_path)


if __name__ == "__main__":
    main()
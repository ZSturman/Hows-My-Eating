import os
import pandas as pd
import json
import uuid

def flatten_motion_data(motion_data):
    """
    Flatten the motion data to convert nested structures into individual columns.
    """
    flattened_data = []
    for entry in motion_data:
        flattened_entry = {
            "timestamp": entry["timestamp"],
            "userAccelerationX": entry["userAcceleration"]["x"],
            "userAccelerationY": entry["userAcceleration"]["y"],
            "userAccelerationZ": entry["userAcceleration"]["z"],
            "gravityX": entry["gravity"]["x"],
            "gravityY": entry["gravity"]["y"],
            "gravityZ": entry["gravity"]["z"],
            "rotationRateX": entry["rotationRate"]["x"],
            "rotationRateY": entry["rotationRate"]["y"],
            "rotationRateZ": entry["rotationRate"]["z"],
            "attitudeYaw": entry["attitude"]["yaw"],
            "attitudeRoll": entry["attitude"]["roll"],
            "attitudePitch": entry["attitude"]["pitch"],
        }
        flattened_data.append(flattened_entry)
    return flattened_data


def filter_and_merge_chew_intervals(chew_intervals, motion_timestamps):
    """
    Filters chew intervals to ensure they fall within the motion data range
    and merges overlapping or adjacent intervals.
    """
    # Get the range of motion data timestamps
    min_motion_timestamp = min(motion_timestamps)
    max_motion_timestamp = max(motion_timestamps)

    # Filter chew intervals to the motion data range
    filtered_intervals = [
        (max(start, min_motion_timestamp), min(end, max_motion_timestamp))
        for start, end in chew_intervals
        if end >= min_motion_timestamp and start <= max_motion_timestamp
    ]

    # Sort intervals and merge overlapping/adjacent intervals
    filtered_intervals.sort()
    merged_intervals = []
    for start, end in filtered_intervals:
        if not merged_intervals or start > merged_intervals[-1][1]:
            merged_intervals.append((start, end))
        else:
            merged_intervals[-1] = (merged_intervals[-1][0], max(merged_intervals[-1][1], end))

    return merged_intervals


def handle_not_chew_intervals(motion_data, chew_intervals, output_folder, motion_json_path, file_prefix):
    """
    Handle not-chew intervals by saving separate CSV files for each interval in the required flat format.
    """
    # Filter and merge chew intervals
    motion_timestamps = [data['timestamp'] for data in motion_data]
    chew_intervals = filter_and_merge_chew_intervals(chew_intervals, motion_timestamps)

    # Compute not-chew intervals
    not_chew_intervals = []
    current_start = motion_timestamps[0]

    for start, end in chew_intervals:
        if current_start < start:
            not_chew_intervals.append((current_start, start))
        current_start = end

    if current_start < motion_timestamps[-1]:
        not_chew_intervals.append((current_start, motion_timestamps[-1]))

    # Save each not-chew interval as a separate CSV file
    csv_files = []
    for idx, (start, end) in enumerate(not_chew_intervals):
        not_chew_data = [data for data in motion_data if start <= data['timestamp'] <= end]
        flattened_data = flatten_motion_data(not_chew_data)  # Flatten the motion data
        df = pd.DataFrame(flattened_data)
        if df.empty:
            continue
        df['file_path'] = motion_json_path

        random_identifier = uuid.uuid4().hex
        output_path = os.path.join(output_folder, f"{file_prefix}_not_chew_{random_identifier}.csv")
        df.to_csv(output_path, index=False)
        csv_files.append(output_path)

    return csv_files

def process_all_not_chew_data(motion_json_path, chew_intervals, output_folder,
                              processed_output_file, processed_rows_output_file,
                              timestamp_col):
    """
    Process the not-chew intervals from a motion JSON file. This function now creates
    two output CSV files: one aggregated and one containing the first, middle, and last rows.
    """
    # Load motion data from JSON
    with open(motion_json_path, 'r') as f:
        motion_data = json.load(f)

    # Step 1: Handle not-chew intervals to create CSV files
    not_chew_csv_files = handle_not_chew_intervals(
        motion_data, chew_intervals, output_folder, motion_json_path, file_prefix="motion"
    )

    # Step 2: For each CSV, process aggregated data and then process row-based data
    for csv_file in not_chew_csv_files:
        # Process aggregated data (as you already do)
        process_csv_file(
            file_path=csv_file,
            output_file=processed_output_file,
            timestamp_col=timestamp_col,
        )
        # Process first, middle, and last rows
        process_csv_file_with_rows(
            file_path=csv_file,
            output_file=processed_rows_output_file,
            exclude_cols=[],  # Adjust if you have specific exclusions
        )
# Function to aggregate data into a single row with corrected column alignment
def aggregate_data_fixed(df, exclude_cols=None):
    if exclude_cols is None:
        exclude_cols = []
    # Select numeric columns, excluding specified columns
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.difference(exclude_cols)
    # Fill NaN values before aggregation
    df[numeric_cols] = df[numeric_cols].fillna(0)
    # Aggregate using mean, max, min, and std
    aggregated = df[numeric_cols].agg(['mean', 'max', 'min', 'std'])
    # Flatten column names to represent the statistic for each feature
    aggregated = aggregated.T.reset_index()
    aggregated.columns = ['feature', 'mean', 'max', 'min', 'std']
    aggregated = aggregated.set_index('feature').stack()
    aggregated.index = ['_'.join(map(str, idx)) for idx in aggregated.index]
    return aggregated

# Function to calculate the interval and append to the aggregated data
def add_interval_column(df, aggregated_data, timestamp_col):
    interval = df[timestamp_col].max() - df[timestamp_col].min()
    aggregated_data['interval'] = interval
    return aggregated_data

# Function to process a single CSV file
def process_csv_file(file_path, output_file, timestamp_col, exclude_cols=[]):
    print("FILE: ", file_path)
    df = pd.read_csv(file_path)

    # Ensure the 'file_path' column does not affect numeric aggregations
    if 'file_path' in df.columns:
        df = df.drop(columns=['file_path'])

    # Aggregate the data
    aggregated = aggregate_data_fixed(df, exclude_cols=exclude_cols)
    # Add the interval column
    aggregated = add_interval_column(df, aggregated.to_frame().T, timestamp_col=timestamp_col)
    # Add the file path as a new column
    aggregated['file_path'] = file_path

    # Validate the number of columns before writing
    if len(aggregated.columns) != len(aggregated.iloc[0]):
        print(f"Warning: Mismatched columns in {file_path}")
        return

    # Append to the output CSV file
    if not os.path.exists(output_file):
        aggregated.to_csv(output_file, index=False)
    else:
        aggregated.to_csv(output_file, mode='a', header=False, index=False)
        
# Function to process "not-chew" chunks in a CSV file and save them to their own CSV file
def process_not_chew_csv_file(file_path, output_file, timestamp_col, exclude_cols=[]):
    df = pd.read_csv(file_path)

    # Ensure the 'file_path' column does not affect numeric aggregations
    if 'file_path' in df.columns:
        df = df.drop(columns=['file_path'])

    # Initialize variables
    not_chew_chunks = []
    current_chunk = []
    previous_label = None

    # Iterate over the rows to identify consecutive "not-chew" chunks
    for idx, row in df.iterrows():
        if row['label'] == 'not-chew':
            current_chunk.append(row)
        elif previous_label == 'not-chew' and row['label'] != 'not-chew':
            # If transitioning out of a "not-chew" chunk, process the current chunk
            if len(current_chunk) >= 10:  # Skip chunks shorter than 10 rows
                chunk_df = pd.DataFrame(current_chunk)
                aggregated = aggregate_data_fixed(chunk_df, exclude_cols=exclude_cols)
                aggregated = add_interval_column(
                    chunk_df, aggregated.to_frame().T, timestamp_col=timestamp_col
                )
                aggregated['file_path'] = file_path
                not_chew_chunks.append(aggregated)
            current_chunk = []  # Reset for the next chunk

        previous_label = row['label']

    # Process the last chunk if it ends with "not-chew"
    if current_chunk and len(current_chunk) >= 10:
        chunk_df = pd.DataFrame(current_chunk)
        aggregated = aggregate_data_fixed(chunk_df, exclude_cols=exclude_cols)
        aggregated = add_interval_column(
            chunk_df, aggregated.to_frame().T, timestamp_col=timestamp_col
        )
        aggregated['file_path'] = file_path
        not_chew_chunks.append(aggregated)

    # Combine all aggregated chunks and save to the output file
    if not_chew_chunks:
        all_aggregated = pd.concat(not_chew_chunks)
        if not os.path.exists(output_file):
            all_aggregated.to_csv(output_file, index=False)
        else:
            all_aggregated.to_csv(output_file, mode='a', header=False, index=False)
    

def process_directory(input_dir, chunk_output_file, motion_output_file, not_chew_output_file, chunk2_output_file, motion2_output_file, not_chew2_output_file):
    processed_motion_files = 0
    processed_chunk_files = 0
    processed_not_chew_files = 0
    
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                if file.startswith("chunk_data"):
                    processed_chunk_files += 1
                    print(f"Processing chunk file: {processed_chunk_files} -  {file_path}")
                    process_csv_file(
                        file_path=file_path,
                        output_file=chunk_output_file,
                        timestamp_col='timestamp',
                    )
                    # Process with rows for chunk data
                    process_csv_file_with_rows(file_path, chunk2_output_file)
                elif file.startswith("motion_data"):
                    processed_motion_files += 1
                    print(f"Processing motion file: {processed_motion_files} -  {file_path}")
                    exclude_cols = ['normalized_timestamp', 'transformedRotationW', 'transformedRotationX', 'transformedRotationY', 'transformedRotationZ']
                    process_csv_file(
                        file_path=file_path,
                        output_file=motion_output_file,
                        timestamp_col='timestamp',
                        exclude_cols=exclude_cols
                    )
                    # Process with rows for motion data
                    process_csv_file_with_rows(file_path, motion2_output_file, exclude_cols=exclude_cols)
                elif file.startswith("labelled_data"):
                    processed_not_chew_files += 1
                    print(f"Processing not-chew file: {processed_not_chew_files} -  {file_path}")
                    exclude_cols = ['status', 'mouth', 'action', 'bite_count', 'chew_count', 'chews_per_bite', 'behind_hand']
                    process_not_chew_csv_file(
                        file_path=file_path,
                        output_file=not_chew_output_file,
                        timestamp_col='timestamp',
                        exclude_cols=exclude_cols
                    )
                    # Process with rows for not-chew data
                    process_csv_file_with_rows(file_path, not_chew2_output_file, exclude_cols=exclude_cols)
    


def process_csv_file_with_rows(file_path, output_file, exclude_cols=None):
    """
    Extract the first, middle, and last rows from the CSV file,
    calculate elapsed times and numeric differences for numeric columns,
    and save the data to the output file.
    """
    if exclude_cols is None:
        exclude_cols = []


    # Load the CSV file
    df = pd.read_csv(file_path)
    
    
    # Remove the excluded columns from the DataFrame
    df = df.drop(columns=exclude_cols, errors='ignore')

    # Skip empty files
    if df.empty:
        print(f"Skipping empty file: {file_path}")
        return

    # Extract the first, middle, and last rows
    first_row = df.iloc[0]
    middle_index = len(df) // 2
    middle_row = df.iloc[middle_index]
    last_row = df.iloc[-1]

    # Calculate elapsed times for the timestamp column
    timestamp_col = 'timestamp'  # Ensure this column exists in your CSV
    elapsed_time_first_to_middle = middle_row[timestamp_col] - first_row[timestamp_col]
    elapsed_time_middle_to_last = last_row[timestamp_col] - middle_row[timestamp_col]

    # Identify numeric columns in the DataFrame
    numeric_columns = df.select_dtypes(include='number').columns

    # Calculate differences for numeric columns between first & middle rows and between middle & last rows
    diff_first_to_middle = {
        f"diff_first_to_middle_{col}": middle_row[col] - first_row[col] for col in numeric_columns
    }
    diff_middle_to_last = {
        f"diff_middle_to_last_{col}": last_row[col] - middle_row[col] for col in numeric_columns
    }

    # Prefix each feature in the rows
    first_row_prefixed = {f"first_row_{col}": value for col, value in first_row.items()}
    middle_row_prefixed = {f"middle_row_{col}": value for col, value in middle_row.items()}
    last_row_prefixed = {f"last_row_{col}": value for col, value in last_row.items()}

    # Combine all extracted data
    extracted_data = {
        "file_path": file_path,
        "elapsed_time_first_to_middle": elapsed_time_first_to_middle,
        "elapsed_time_middle_to_last": elapsed_time_middle_to_last,
        **first_row_prefixed,
        **middle_row_prefixed,
        **last_row_prefixed,
        **diff_first_to_middle,
        **diff_middle_to_last,
    }

    # Convert the extracted data to a DataFrame and append to the output CSV file
    extracted_df = pd.DataFrame([extracted_data])
    if not os.path.exists(output_file):
        extracted_df.to_csv(output_file, index=False)
    else:
        extracted_df.to_csv(output_file, mode='a', header=False, index=False)

    print(f"Processed and saved: {file_path}")



# Specify the input directory and output files
main_dir = '/Users/zacharysturman/Desktop/export'
input_dirs = ['2025Feb07-153854', '2025Feb06-175748', '2025Feb06-113058']

chunk_output_file = os.path.join(main_dir, 'aggregated_chunk_data_chew.csv')
chunk2_output_file = os.path.join(main_dir, 'aggregated_chunk_data_chew2.csv')

motion_output_file = os.path.join(main_dir, 'aggregated_motion_data_chew.csv')
motion2_output_file = os.path.join(main_dir, 'aggregated_motion_data_chew2.csv')

not_chew_output_file = os.path.join(main_dir, 'aggregated_chunk_data_not_chew.csv')
processed_not_chew_output_file = os.path.join(main_dir, 'aggregated_motion_data_not_chew.csv')
not_chew2_output_file = os.path.join(main_dir, 'aggregated_chunk_data_not_chew2.csv')
processed_not_chew2_output_file = os.path.join(main_dir, 'aggregated_motion_data_not_chew2.csv')

not_chew_output_folder = os.path.join(main_dir, 'not_chew_motion_data')

# Make the output directory if it does not exist
if not os.path.exists(not_chew_output_folder):
    os.makedirs(not_chew_output_folder)

for input_dir in input_dirs:
    input_directory = os.path.join(main_dir, input_dir)
    process_directory(
        input_directory,
        chunk_output_file,
        motion_output_file,
        not_chew_output_file,
        chunk2_output_file,
        motion2_output_file,
        not_chew2_output_file
    )
# now load in the motion_output_file,
motion_df = pd.read_csv(motion_output_file)

for input_dir in input_dirs:
    input_directory = os.path.join(main_dir, input_dir)
    motion_df_subset = motion_df[motion_df['file_path'].notna() & motion_df['file_path'].str.startswith(input_directory)]
    chew_intervals = []
    for idx, row in motion_df_subset.iterrows():
        chew_intervals.append((row['timestamp_min'], row['timestamp_max']))

    for input_dir in input_dirs:
        input_directory = os.path.join(main_dir, input_dir)
        motion_data_json_path = os.path.join(input_directory, 'extra', f'{input_dir}.json')

        # Process not-chew intervals for the current motion JSON file, including row extraction
        process_all_not_chew_data(
            motion_json_path=motion_data_json_path,
            chew_intervals=chew_intervals,
            output_folder=not_chew_output_folder,
            processed_output_file=processed_not_chew_output_file,
            processed_rows_output_file=processed_not_chew2_output_file,
            timestamp_col='timestamp',
        )
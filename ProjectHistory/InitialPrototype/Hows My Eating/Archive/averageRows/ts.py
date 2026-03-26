"""
This script processes a folder structure containing "export" and "sorted" directories.
For each subfolder (folder_x) in the "export" directory, it performs the following steps:

1. Finds the CSV file starting with "labelled_data" in folder_x and extracts timestamp ranges.
2. Loads and preprocesses motion data from a JSON file located in folder_x/extra (named folder_x.json).
3. Splits the motion data into subsets (chewing segments) based on the extracted timestamps,
   and saves each subset as a CSV file in a "chewing" folder within folder_x. Each output CSV file
   is given a unique UUID in its filename.
4. Finds the "not_chew" CSV file in folder_x, splits it into subsets matching the row counts
   (lengths) of the chewing CSV files, and saves each subset as a CSV file in a "not-chewing" folder
   within folder_x. If there are not enough rows for any subset, the remaining rows are used and a
   message is printed.
5. Copies the "chewing" and "not-chewing" folders from folder_x to the "sorted" directory. If folders
   with those names already exist in "sorted", an underscore and an incremented number are appended.
6. Moves the entire folder_x from its original location to the "sorted/raw" folder, avoiding name conflicts
   by appending an underscore and an incremented number if necessary.

Usage:
    python script.py <base_folder_path>

The base folder should contain two subdirectories:
    - export
    - sorted

Inside "export", there are one or more uniquely named folders (folder_x). Each folder_x must contain:
    - A CSV file starting with "labelled_data" (used to extract timestamps).
    - A "not_chew" CSV file (used for splitting not-chewing data).
    - An "extra" folder containing a JSON file named exactly as folder_x (for motion data).

Inside "sorted", there should be at least the following subdirectories (though the script does not modify these):
    - raw
    - test
    - train

All output CSV files are given unique identifiers to prevent file conflicts.
"""



import os
import sys
import csv
import json
import uuid
import shutil
from collections import defaultdict
from typing import Dict, List, Any

import pandas as pd


def extract_timestamps(csv_file_path: str) -> Dict[int, Dict[str, float]]:
    """
    Extract start and end timestamps for each bite count from the labelled_data CSV file.

    Args:
        csv_file_path (str): Path to the labelled_data CSV file.

    Returns:
        Dict[int, Dict[str, float]]: Mapping from bite count to a dictionary with 'start' and 'end' timestamps.
    """
    timestamps = defaultdict(lambda: {"start": float("inf"), "end": float("-inf")})
    with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                bite_count = int(row["bite_count"])
                timestamp = float(row["timestamp"])
                if bite_count == 0:
                    continue
                timestamps[bite_count]["start"] = min(timestamps[bite_count]["start"], timestamp)
                timestamps[bite_count]["end"] = max(timestamps[bite_count]["end"], timestamp)
            except (ValueError, KeyError):
                continue
    return dict(timestamps)


def save_json(data: Any, json_file_path: str) -> str:
    """
    Save the given data as a JSON file.

    Args:
        data (Any): The data to save.
        json_file_path (str): The file path where JSON data will be written.

    Returns:
        str: The JSON string that was written.
    """
    with open(json_file_path, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=4)
    return json.dumps(data)


def find_csv_files_starting_with(directory: str, prefix: str) -> List[str]:
    """
    Find CSV files in the specified directory whose names start with the given prefix.

    Args:
        directory (str): Directory to search in.
        prefix (str): Filename prefix to match.

    Returns:
        List[str]: A list of CSV filenames matching the prefix.
    """
    return [
        file
        for file in os.listdir(directory)
        if file.startswith(prefix) and file.lower().endswith(".csv")
    ]

def find_json_files_starting_with(directory: str, prefix: str) -> List[str]:
    """
    Find JSON files in the specified directory whose names start with the given prefix.

    Args:
        directory (str): Directory to search in.
        prefix (str): Filename prefix to match.

    Returns:
        List[str]: A list of JSON filenames matching the prefix.
    """
    return [
        file
        for file in os.listdir(directory)
        if file.startswith(prefix) and file.lower().endswith(".json")
    ]

def create_dataframe_from_json(json_file_path: str) -> pd.DataFrame:
    """
    Load JSON data from the specified file and convert it into a pandas DataFrame.

    Args:
        json_file_path (str): Path to the JSON file.

    Returns:
        pd.DataFrame: A DataFrame constructed from the JSON data.
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return pd.DataFrame(data)


def preprocess_motion_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess a motion data DataFrame by normalizing timestamps and flattening nested fields.

    The function performs the following operations:
      - Normalizes the 'timestamp' column so that it starts at 0.
      - Drops the 'transformedRotation' column if present.
      - Splits nested fields (userAcceleration, gravity, rotationRate, attitude) into separate columns.

    Args:
        df (pd.DataFrame): The original motion data DataFrame.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"] - df["timestamp"].min()

    # Remove unnecessary column if it exists
    df = df.drop(columns=["transformedRotation"], errors="ignore")

    # Flatten nested fields into separate columns
    for field in ["userAcceleration", "gravity", "rotationRate", "attitude"]:
        if field in df.columns:
            if not df[field].empty and isinstance(df[field].iloc[0], dict):
                for axis in ["x", "y", "z"]:
                    if axis in df[field].iloc[0]:
                        df[f"{field}_{axis}"] = df[field].apply(lambda x: x.get(axis, None))
                if field == "attitude":
                    for angle in ["roll", "pitch", "yaw"]:
                        df[f"{field}_{angle}"] = df[field].apply(lambda x: x.get(angle, None))
            df = df.drop(columns=[field])
    return df


def split_and_save_motion_data(
    motion_df: pd.DataFrame, timestamps: Dict[int, Dict[str, float]], folder_path: str
) -> List[int]:
    """
    Split motion data into subsets based on provided timestamp ranges and save each subset as a CSV file.

    Each CSV file is saved into a "chewing" folder within folder_path, and a unique UUID is appended
    to its filename to prevent conflicts.

    Args:
        motion_df (pd.DataFrame): The preprocessed motion data DataFrame.
        timestamps (Dict[int, Dict[str, float]]): Dictionary mapping bite count to timestamp ranges.
        folder_path (str): Path to the folder (folder_x) where the "chewing" folder will be created.

    Returns:
        List[int]: A list of row counts for each created chewing CSV file.
    """
    chewing_folder = os.path.join(folder_path, "chewing")
    os.makedirs(chewing_folder, exist_ok=True)
    chewing_lengths = []

    for key, time_range in timestamps.items():
        start_time = time_range["start"]
        end_time = time_range["end"]

        # Extract rows where the timestamp is within the specified range
        subset = motion_df[
            (motion_df["timestamp"] >= start_time) & (motion_df["timestamp"] <= end_time)
        ]
        num_rows = len(subset)
        chewing_lengths.append(num_rows)

        # Append a unique UUID to the filename
        unique_id = uuid.uuid4().hex
        output_file = os.path.join(chewing_folder, f"motion_data_{key}_rows_{num_rows}_{unique_id}.csv")
        subset.to_csv(output_file, index=False)
        print(f"Saved chewing CSV: {output_file}")

    return chewing_lengths


def split_and_save_not_chewing_data(
    not_chew_df: pd.DataFrame, lengths: List[int], folder_path: str
) -> None:
    """
    Split the not-chewing data into subsets matching the specified lengths and save each subset as a CSV file.

    Each CSV file is saved into a "not-chewing" folder within folder_path, and a unique UUID is appended
    to its filename. If there are not enough rows for a given length, the available rows are used and
    a message is printed.

    Args:
        not_chew_df (pd.DataFrame): DataFrame loaded from the not_chew CSV file.
        lengths (List[int]): List of row counts corresponding to the chewing CSV files.
        folder_path (str): Path to the folder (folder_x) where the "not-chewing" folder will be created.
    """
    not_chewing_folder = os.path.join(folder_path, "not-chewing")
    os.makedirs(not_chewing_folder, exist_ok=True)

    start_idx = 0
    total_rows = len(not_chew_df)

    for i, length in enumerate(lengths):
        end_idx = start_idx + length
        if start_idx >= total_rows:
            print("No more rows available in not_chew data.")
            break
        if end_idx > total_rows:
            print(
                f"Not enough rows for subset {i+1}: Requested {length}, available {total_rows - start_idx}. Using available rows."
            )
            end_idx = total_rows

        subset = not_chew_df.iloc[start_idx:end_idx]
        unique_id = uuid.uuid4().hex
        output_file = os.path.join(
            not_chewing_folder, f"not_chewing_subset_{i+1}_rows_{len(subset)}_{unique_id}.csv"
        )
        subset.to_csv(output_file, index=False)
        print(f"Saved not-chewing CSV: {output_file}")

        start_idx = end_idx


def get_non_conflicting_path(base_dir: str, folder_name: str) -> str:
    """
    Generate a non-conflicting folder path by appending an underscore and a number if necessary.

    Args:
        base_dir (str): The base directory where the folder is to be located.
        folder_name (str): Desired folder name.

    Returns:
        str: A folder path that does not conflict with existing folders.
    """
    candidate = os.path.join(base_dir, folder_name)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(base_dir, f"{folder_name}_{counter}")
        counter += 1
    return candidate


def copy_folder_to_sorted(source_folder: str, sorted_dir: str, folder_label: str) -> None:
    """
    Copy the specified folder to the sorted directory with a non-conflicting name.

    Args:
        source_folder (str): Path of the folder to be copied.
        sorted_dir (str): The target sorted directory.
        folder_label (str): Label for the folder (e.g., 'chewing' or 'not-chewing').
    """
    dest_folder = get_non_conflicting_path(sorted_dir, folder_label)
    shutil.copytree(source_folder, dest_folder)
    print(f"Copied folder '{source_folder}' to '{dest_folder}'.")


def move_folder_to_sorted_raw(source_folder: str, sorted_dir: str) -> None:
    """
    Move the entire folder (folder_x) to the sorted/raw directory with a non-conflicting name.

    Args:
        source_folder (str): Path of the folder to be moved.
        sorted_dir (str): The base sorted directory where the 'raw' subfolder exists.
    """
    raw_dir = os.path.join(sorted_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    folder_name = os.path.basename(source_folder)
    dest_folder = get_non_conflicting_path(raw_dir, folder_name)
    shutil.move(source_folder, dest_folder)
    print(f"Moved folder '{source_folder}' to '{dest_folder}'.")


def process_folder(folder_path: str) -> None:
    """
    Process a single folder (folder_x) from the export directory.

    The function performs the following:
      1. Finds the labelled_data CSV file and extracts timestamps.
      2. Loads and preprocesses motion data from the corresponding JSON file in 'extra'.
      3. Splits and saves chewing motion data based on timestamps, adding unique UUIDs to filenames.
      4. Loads the not_chew CSV file, splits it into subsets matching the chewing CSV lengths, and saves them.

    Args:
        folder_path (str): The path of the folder to process (e.g., export/folder_x).
    """
    # Step 1: Process the labelled_data CSV file for timestamps.
    labelled_csv_files = find_csv_files_starting_with(folder_path, "labelled_data")
    if not labelled_csv_files:
        print(f"No labelled_data CSV found in {folder_path}. Skipping folder.")
        return
    labelled_csv_path = os.path.join(folder_path, labelled_csv_files[0])
    timestamps = extract_timestamps(labelled_csv_path)
    # Optionally save the extracted timestamps as JSON for reference.
    timestamps_json_path = os.path.join(folder_path, "timestamps.json")
    save_json(timestamps, timestamps_json_path)
    print(f"Extracted timestamps from {labelled_csv_path}.")

    # Step 2: Load and preprocess motion data from the JSON file in the 'extra' folder.
    folder_name = os.path.basename(folder_path)
    extra_folder = os.path.join(folder_path, "extra")
    motion_json_file = os.path.join(extra_folder, f"{folder_name}.json")
    if not os.path.exists(motion_json_file):
        print(f"Motion data JSON file {motion_json_file} not found in {folder_path}. Skipping folder.")
        return
    motion_df = create_dataframe_from_json(motion_json_file)
    motion_df = preprocess_motion_data(motion_df)

    # Step 3: Split motion data into chewing segments and save to the "chewing" folder.
    chewing_lengths = split_and_save_motion_data(motion_df, timestamps, folder_path)

    # Step 4: Process the not_chew CSV file and split it into subsets matching chewing lengths.
    not_chew_files = find_json_files_starting_with(folder_path, "not_chew")
    if not not_chew_files:
        print(f"No not_chew CSV found in {folder_path}. Skipping not-chewing data processing.")
    else:
        not_chew_csv_path = os.path.join(folder_path, not_chew_files[0])
        try:
            not_chew_df = pd.read_json(not_chew_csv_path)
        except Exception as e:
            print(f"Error reading {not_chew_csv_path}: {e}")
            return
        not_chew_df = preprocess_motion_data(not_chew_df)
        split_and_save_not_chewing_data(not_chew_df, chewing_lengths, folder_path)


def main() -> None:
    """
    Main function to process all export folders and organize sorted data.

    The script accepts a single command-line argument specifying the base folder path.
    It expects this base folder to contain 'export' and 'sorted' directories.
    For each folder in 'export', the function processes the folder, copies the newly created
    "chewing" and "not-chewing" folders to the sorted directory, and then moves the entire folder
    to the sorted/raw directory.
    """
    if len(sys.argv) != 2:
        print("Usage: python script.py <base_folder_path>")
        sys.exit(1)

    base_path = sys.argv[1]
    export_dir = os.path.join(base_path, "export")
    sorted_dir = os.path.join(base_path, "sorted")

    if not os.path.exists(export_dir):
        print(f"Export directory not found at {export_dir}.")
        sys.exit(1)
    if not os.path.exists(sorted_dir):
        print(f"Sorted directory not found at {sorted_dir}.")
        sys.exit(1)

    # Process each folder in the export directory.
    for folder in os.listdir(export_dir):
        folder_path = os.path.join(export_dir, folder)
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_path}")
            process_folder(folder_path)

            # After processing, copy the "chewing" and "not-chewing" folders to the sorted directory.
            chewing_folder = os.path.join(folder_path, "chewing")
            not_chewing_folder = os.path.join(folder_path, "not-chewing")
            if os.path.exists(chewing_folder):
                copy_folder_to_sorted(chewing_folder, sorted_dir, "chewing")
            if os.path.exists(not_chewing_folder):
                copy_folder_to_sorted(not_chewing_folder, sorted_dir, "not-chewing")

            # Finally, move the entire folder_x to the sorted/raw folder.
            move_folder_to_sorted_raw(folder_path, sorted_dir)


if __name__ == "__main__":
    main()
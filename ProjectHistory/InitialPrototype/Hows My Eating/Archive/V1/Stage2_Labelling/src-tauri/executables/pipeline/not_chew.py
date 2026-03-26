import os
import json
import csv
import numpy as np

def load_json(filename: str) -> list:
    with open(filename, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON data should be a list of records.")
    return data

def group_records(data: list, desired_rows: int = 15, tolerance: int = 2) -> list:
    """
    Group records so that each group contains approximately the desired number of rows,
    within a tolerance range.

    :param data: List of records to group.
    :param desired_rows: Target number of rows per group.
    :param tolerance: Allowed variation in the number of rows per group.
    :return: A list of grouped records.
    """
    sorted_data = sorted(data, key=lambda rec: rec["timestamp"])
    groups = []
    current_group = []

    for rec in sorted_data:
        current_group.append(rec)

        # Check if the current group is within the desired range
        if len(current_group) >= desired_rows - tolerance:
            # Stop adding records if the group exceeds the upper bound
            if len(current_group) >= desired_rows + tolerance:
                groups.append(current_group)
                current_group = []
    
    # Add the last group if it has any remaining records
    if current_group:
        groups.append(current_group)
    
    return groups

def extract_row(rec: dict, global_start: float, label: str = "NotChew") -> dict:
    """
    Extract a flat dictionary from a record with keys in the order required by the CSV.
    The CSV columns are:
      timestamp,
      userAccelerationX, userAccelerationY, userAccelerationZ,
      gravityZ, gravityY, gravityX,
      transformedRotationY, transformedRotationW, transformedRotationX, transformedRotationZ,
      rotationRateZ, rotationRateX, rotationRateY,
      attitudeRoll, attitudeYaw, attitudePitch,
      normalized_timestamp, label
    """
    # Use dict.get to allow for missing keys (defaulting to empty string)
    ua = rec.get("userAcceleration", {})
    grav = rec.get("gravity", {})
    tr = rec.get("transformedRotation", {})
    rr = rec.get("rotationRate", {})
    att = rec.get("attitude", {})

    row = {
        "timestamp": rec.get("timestamp", ""),
        "userAccelerationX": ua.get("x", ""),
        "userAccelerationY": ua.get("y", ""),
        "userAccelerationZ": ua.get("z", ""),
        # Note the CSV expects gravity in the order: Z, Y, X.
        "gravityZ": grav.get("z", ""),
        "gravityY": grav.get("y", ""),
        "gravityX": grav.get("x", ""),
        # Transformed rotation order: Y, W, X, Z.
        "transformedRotationY": tr.get("y", ""),
        "transformedRotationW": tr.get("w", ""),
        "transformedRotationX": tr.get("x", ""),
        "transformedRotationZ": tr.get("z", ""),
        # Rotation rate order: Z, X, Y.
        "rotationRateZ": rr.get("z", ""),
        "rotationRateX": rr.get("x", ""),
        "rotationRateY": rr.get("y", ""),
        # Attitude order: Roll, Yaw, Pitch.
        "attitudeRoll": att.get("roll", ""),
        "attitudeYaw": att.get("yaw", ""),
        "attitudePitch": att.get("pitch", ""),
        "normalized_timestamp": rec.get("timestamp", 0) - global_start,
        "label": label
    }
    return row

def write_csv(filename: str, rows: list, header: list) -> None:
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def export_not_chews(directory: str, output_dir: str, logger)-> dict:
    """
    Export records from JSON files in the given directory to CSV files.
    Each CSV file contains records grouped by a maximum interval of 1.5 seconds.
    The output directory structure is as follows:
    output_dir
    ├── Not-Chew
    │   ├── 1.csv
    │   ├── 2.csv
    
    Args:
        directory (str): Path to the directory containing JSON files.
        output_dir (str): Path to the output directory.
        logger: Logger instance for logging messages.
        
    Returns:
        dict: A dictionary containing the status, file paths, and error details (if any).
    """
    result = {
        "status": "success",
        "files": [],
        "error": None,
    }
    try:
        files = os.listdir(directory)
        
        for file in files:
            # if the file is a .json file
            if file.endswith(".json"):
                # load the json file
                data = load_json(f"{directory}/{file}")
                
                # Determine the global start timestamp (used for normalization)
                global_start = min(rec["timestamp"] for rec in data)
                logger.info(f"Global start timestamp: {global_start}")

                # Group records so that each group spans no more than 1.5 seconds
                groups = group_records(data)

                # Define the header for the CSV files (order matters)
                header = [
                    "timestamp",
                    "userAccelerationX", "userAccelerationY", "userAccelerationZ",
                    "gravityZ", "gravityY", "gravityX",
                    "transformedRotationY", "transformedRotationW", "transformedRotationX", "transformedRotationZ",
                    "rotationRateZ", "rotationRateX", "rotationRateY",
                    "attitudeRoll", "attitudeYaw", "attitudePitch",
                    "normalized_timestamp", "label"
                ]

                # Set the constant label; change if needed.
                constant_label = "NotChew"
                
                not_chew_folder = f"{output_dir}/Not-Chew"
                # Create not chew folder
                os.makedirs(not_chew_folder, exist_ok=True)
                logger.info(f"Created folder: {not_chew_folder}")

                # Call the function with a desired row count and tolerance
                groups = group_records(data, desired_rows=15, tolerance=2)

                # Process the grouped data as before
                for i, group in enumerate(groups, start=1):
                    rows = [extract_row(rec, global_start, constant_label) for rec in group]
                    random_identifier = np.random.randint(1000)
                    output_filename = f"{not_chew_folder}/{random_identifier}.csv"
                    write_csv(output_filename, rows, header)
                    logger.info(f"Saved {len(rows)} records to {output_filename}")
                    
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        result["status"] = "failure"
        result["error"] = str(e)
    return result
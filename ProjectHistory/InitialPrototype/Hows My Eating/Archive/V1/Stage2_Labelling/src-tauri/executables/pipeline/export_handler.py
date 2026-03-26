from typing import List
import os
import pandas as pd
import json
import numpy as np
import logging
import uuid

def export_file_handler(
    output_folder_dir: str,
    motion_data_file: str,
    mov_info_file: str,
    ratios_data_file: str,
    points_data_file: str,
    merged_data_file: str,
    chunks_dir: str,
    chunks_records: str,
    logger
) -> List[str]:
    """
    Processes and exports labelled CSV data and corresponding motion data based on provided file paths.
    
    This function reads various data files including motion data, movement info, ratios data, merged data,
    chunks records, and points data. It performs several processing steps including merging data frames, 
    normalizing timestamps, and segmenting the data based on specified frame ranges. The processed data is 
    saved to CSV files, and a list of movement file records is returned.
    
    Args:
        output_folder_dir (str): Directory where the labelled output folders will be created.
        motion_data_file (str): Path to the motion data JSON file.
        mov_info_file (str): Path to the movement info JSON file.
        ratios_data_file (str): Path to the ratios data CSV file.
        points_data_file (str): Path to the points data CSV file.
        merged_data_file (str): Path to the merged data CSV file.
        chunks_dir (str): Directory where the chunks info will be saved.
        chunks_records (str): Path to the chunks records CSV file.
        logger: Logger instance for logging messages.
        
    Returns:
        List[str]: A list of dictionaries, each containing 'folder_path' and 'file_path'
                   for files to be copied. Returns an empty list if an error occurs.
    """
    try:
        # Read movement info file
        with open(mov_info_file, 'r') as f:
            mov_info = json.load(f)
        logger.info(f"Loaded movement info from: {mov_info_file}")

        # Read motion data file
        with open(motion_data_file, 'r') as f:
            motion_data = json.load(f)
        logger.info(f"Loaded motion data from: {motion_data_file}")

        # Convert motion data to a DataFrame
        motion_df = pd.DataFrame(motion_data)

        # --- Begin: Expand nested motion data columns ---
        if 'userAcceleration' in motion_df.columns:
            user_accel = motion_df['userAcceleration'].apply(pd.Series)
            user_accel = user_accel.rename(columns={
                'x': 'userAccelerationX',
                'y': 'userAccelerationY',
                'z': 'userAccelerationZ'
            })
            motion_df = pd.concat([motion_df.drop(columns=['userAcceleration']), user_accel], axis=1)

        if 'gravity' in motion_df.columns:
            gravity = motion_df['gravity'].apply(pd.Series)
            gravity = gravity.rename(columns={
                'x': 'gravityX',
                'y': 'gravityY',
                'z': 'gravityZ'
            })
            motion_df = pd.concat([motion_df.drop(columns=['gravity']), gravity], axis=1)

        if 'transformedRotation' in motion_df.columns:
            transformed_rotation = motion_df['transformedRotation'].apply(pd.Series)
            transformed_rotation = transformed_rotation.rename(columns={
                'x': 'transformedRotationX',
                'y': 'transformedRotationY',
                'z': 'transformedRotationZ',
                'w': 'transformedRotationW'
            })
            motion_df = pd.concat([motion_df.drop(columns=['transformedRotation']), transformed_rotation], axis=1)

        if 'rotationRate' in motion_df.columns:
            rotation_rate = motion_df['rotationRate'].apply(pd.Series)
            rotation_rate = rotation_rate.rename(columns={
                'x': 'rotationRateX',
                'y': 'rotationRateY',
                'z': 'rotationRateZ'
            })
            motion_df = pd.concat([motion_df.drop(columns=['rotationRate']), rotation_rate], axis=1)
            
        if 'attitude' in motion_df.columns:
            attitude = motion_df['attitude'].apply(pd.Series)
            attitude = attitude.rename(columns={
                'pitch': 'attitudePitch',
                'roll': 'attitudeRoll',
                'yaw': 'attitudeYaw'
            })
            motion_df = pd.concat([motion_df.drop(columns=['attitude']), attitude], axis=1)
        # --- End: Expand nested motion data columns ---

        # Read CSV files
        ratios_df = pd.read_csv(ratios_data_file)
        logger.info(f"Loaded ratios data from: {ratios_data_file}")

        merged_df = pd.read_csv(merged_data_file)
        logger.info(f"Loaded merged data from: {merged_data_file}")

        records_df = pd.read_csv(chunks_records)
        logger.info(f"Loaded chunks records from: {chunks_records}")

        points_df = pd.read_csv(points_data_file)
        logger.info(f"Loaded points data from: {points_data_file}")

        # Step 1: Adjust ratios data if the first frame is 0
        if not ratios_df.empty and ratios_df.iloc[0]['frame'] == 0:
            ratios_df = ratios_df.iloc[1:]
            logger.info("Dropped first row of ratios data because 'frame' was 0.")

        # Drop 'timestamp' column from points data
        if 'timestamp' in points_df.columns:
            points_df = points_df.drop(columns=['timestamp'])
            logger.info("Dropped 'timestamp' column from points data.")

        # Step 2: Merge data frames to create labelled CSV data
        labelled_csv_data = pd.merge(ratios_df, merged_df, on='frame')
        labelled_csv_data = pd.merge(labelled_csv_data, points_df, on='frame')
        
                # Add a "label" column with default value "not-chew"
        labelled_csv_data["label"] = "not-chew"
        # For every record, update the label to "chew" for rows whose frame is in between start_frame and end_frame.
        for _, record in records_df.iterrows():
            start_frame = record['start_frame']
            end_frame = record['end_frame']
            labelled_csv_data.loc[
                (labelled_csv_data['frame'] >= start_frame) & (labelled_csv_data['frame'] <= end_frame),
                "label"
            ] = "chew"
        
        

        movs_to_copy_over = []

        # Normalize motion data timestamps
        motion_df['normalized_timestamp'] = motion_df['timestamp'] - motion_df['timestamp'].iloc[0]
        logger.info("Normalized motion data timestamps.")

        # Step 7: Validate final timestamp against mov_info duration
        final_timestamp = motion_df['normalized_timestamp'].iloc[-1]
        expected_duration = mov_info.get('duration', 0)
        if final_timestamp != expected_duration:
            diff = abs(final_timestamp - expected_duration)
            if diff > 0.001:
                logger.error(f"Final timestamp is not close to mov_info.duration. Difference: {diff}")
            elif diff < 0.001:
                logger.info(f"Final timestamp is very close to mov_info.duration. Difference: {diff}")
        else:
            logger.info(f"Final timestamp equals mov_info.duration. Final Timestamp: {final_timestamp}, mov_info.duration: {expected_duration}")

        # Initialize counters for bite and chew counts
        prev_bite_count = 0
        chew_count = 0

        # Step 3: Process each record in the chunks records
        for index, row in records_df.iterrows():
            frame = row['start_frame']
            labelled_row = labelled_csv_data[labelled_csv_data['frame'] == frame]
            if labelled_row.empty:
                logger.warning(f"No matching labelled data found for frame: {frame}")
                continue

            # Adjust bite_count so it starts at 1 instead of 0.
            bite_count = round(labelled_row['bite_count'].values[0]) + 1

            if prev_bite_count != bite_count:
                chew_count = 0
                prev_bite_count = bite_count
            chew_count += 1

            folder_name = f'Bite{bite_count}_Chew{chew_count}_Frame{frame}'
            folder_path = os.path.join(output_folder_dir, "labelled", folder_name)
            
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Created folder: {folder_path}")

            mov_to_copy = {
                'folder_path': folder_path,
                'file_path': row['file_path']
            }
            movs_to_copy_over.append(mov_to_copy)

            # Step 4: Extract chunk data and save as CSV
            start_frame = row['start_frame']
            end_frame = row['end_frame']
            chunk_data = labelled_csv_data[(labelled_csv_data['frame'] >= start_frame) & (labelled_csv_data['frame'] <= end_frame)]
            chunk_csv_path = os.path.join(folder_path, 'chunk_data.csv')
            chunk_data["label"] = "Chew"
            # Drop the unwanted columns
            chunk_data = chunk_data.drop(columns=['status', 'bite_count', 'chew_count', 'chews_per_bite'])
            chunk_data.to_csv(chunk_csv_path, index=False)
            logger.info(f"Saved chunk data CSV to: {chunk_csv_path}")

            # Determine start and end time from chunk data
            start_time = chunk_data.iloc[0]['timestamp']
            end_time = chunk_data.iloc[-1]['timestamp']

            # Find corresponding timestamps in motion data
            start_timestamp_rows = motion_df[motion_df['normalized_timestamp'] >= start_time]
            if start_timestamp_rows.empty:
                logger.warning(f"No motion data found for start time: {start_time}")
                continue
            start_timestamp = start_timestamp_rows.iloc[0]['timestamp']

            end_timestamp_rows = motion_df[motion_df['normalized_timestamp'] <= end_time]
            if end_timestamp_rows.empty:
                logger.warning(f"No motion data found for end time: {end_time}")
                continue
            end_timestamp = end_timestamp_rows.iloc[-1]['timestamp']

            # Get the subset of motion data within the original timestamp range
            subset = motion_df[(motion_df['timestamp'] >= start_timestamp) & (motion_df['timestamp'] <= end_timestamp)]
            if subset.empty:
                logger.warning(f"No motion data found for timestamps between {start_timestamp} and {end_timestamp}")
                continue

            # Get the first and last indices of the subset
            first_idx = subset.index[0]
            last_idx = subset.index[-1]   

            # Extend the range by including up to 10 rows before and 10 rows after (if they exist)
            start_idx = max(0, first_idx - 1)
            end_idx = min(len(motion_df) - 1, last_idx + 1)

            # Extract the extended subset (make a copy to avoid SettingWithCopy warnings)
            extended_timestamps = motion_df.iloc[start_idx:end_idx + 1].copy()
            extended_timestamps["label"] = "Chew"

            # Save the extended motion data CSV to the folder_path
            random_identifier = uuid.uuid4().hex
            motion_csv_path = os.path.join(folder_path, f'motion_data_{random_identifier}.csv')
            extended_timestamps.to_csv(motion_csv_path, index=False)
            logger.info(f"Saved extended motion data CSV to: {motion_csv_path}")

        # Save the list of movement files to copy over as a JSON file
        to_copy_path = os.path.join(chunks_dir, 'to_copy.json')
        labelled_csv_data.to_csv(os.path.join(output_folder_dir, 'labelled_data.csv'), index=False)
        with open(to_copy_path, 'w') as f:
            json.dump(movs_to_copy_over, f)
        logger.info(f"Saved movs_to_copy_over to: {to_copy_path}")

        logger.info(f"export_file_handler completed successfully. Processed {len(movs_to_copy_over)} records.")
        return movs_to_copy_over

    except Exception as e:
        logger.error(f"Error in export_file_handler: {e}", exc_info=True)
        return []
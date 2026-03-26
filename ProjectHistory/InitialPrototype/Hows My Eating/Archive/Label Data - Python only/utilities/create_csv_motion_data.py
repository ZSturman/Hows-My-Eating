import pandas as pd
import json
import sys
import os

def create_csv_from_json(json_path):
    try:
        # Read the JSON data from the file
        with open(json_path, 'r') as file:
            data = json.load(file)

        # Total number of entries
        total_entries = len(data)

        # Prepare data for DataFrame
        rows = []
        prev_timestamp = data[0]['timestamp'] if total_entries > 0 else 0
        mov_timestamp = 0

        # Define frame duration for 30 fps (1/30th of a second)
        frame_duration = 1 / 30.0
        frame_index = 0

        for index, entry in enumerate(data):
            current_timestamp = entry.get('timestamp', 0)
            if index > 0:
                mov_timestamp += current_timestamp - prev_timestamp
            prev_timestamp = current_timestamp

            # Calculate the frame index based on the mov_timestamp
            frame_index = int(mov_timestamp / frame_duration)

            row = {
                'timestamp': float(current_timestamp),
                'movTimestamp': mov_timestamp,
                'frameIndex': frame_index,
                'frameTimestamp': '',
                'isLabelled': '',
                'isEating': '',
                'mouthState': '',
                'isTalking': '',
                'primaryBodyState': '',
                'bodyAction': '',
                'otherLabels': '',
                'gravityX': entry.get('gravity', {}).get('x', None),
                'gravityY': entry.get('gravity', {}).get('y', None),
                'gravityZ': entry.get('gravity', {}).get('z', None),
                'transformedRotationX': entry.get('transformedRotation', {}).get('x', None),
                'transformedRotationY': entry.get('transformedRotation', {}).get('y', None),
                'transformedRotationZ': entry.get('transformedRotation', {}).get('z', None),
                'transformedRotationW': entry.get('transformedRotation', {}).get('w', None),
                'rotationRateX': entry.get('rotationRate', {}).get('x', None),
                'rotationRateY': entry.get('rotationRate', {}).get('y', None),
                'rotationRateZ': entry.get('rotationRate', {}).get('z', None),
                'userAccelerationX': entry.get('userAcceleration', {}).get('x', None),
                'userAccelerationY': entry.get('userAcceleration', {}).get('y', None),
                'userAccelerationZ': entry.get('userAcceleration', {}).get('z', None),
                'attitudeRoll': entry.get('attitude', {}).get('roll', None),
                'attitudePitch': entry.get('attitude', {}).get('pitch', None),
                'attitudeYaw': entry.get('attitude', {}).get('yaw', None),
            }
            rows.append(row)

        # Create a DataFrame
        df = pd.DataFrame(rows)

        # Convert numeric columns to appropriate types
        numeric_columns = [
            'timestamp', 'movTimestamp', 'gravityX', 'gravityY', 'gravityZ',
            'transformedRotationX', 'transformedRotationY', 'transformedRotationZ',
            'transformedRotationW', 'rotationRateX', 'rotationRateY', 'rotationRateZ',
            'userAccelerationX', 'userAccelerationY', 'userAccelerationZ',
            'attitudeRoll', 'attitudePitch', 'attitudeYaw'
        ]
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

        # Interpolate missing frame indexes
        new_rows = []
        for i in range(1, len(df)):
            current_frame_index = df.loc[i, 'frameIndex']
            previous_frame_index = df.loc[i - 1, 'frameIndex']

            # Check for missing frame indexes
            if current_frame_index - previous_frame_index > 1:
                missing_frames = current_frame_index - previous_frame_index - 1
                for j in range(1, missing_frames + 1):
                    # Calculate interpolated values
                    new_frame_index = previous_frame_index + j
                    interpolated_row = {}
                    for column in df.columns:
                        if column == 'frameIndex':
                            interpolated_row[column] = new_frame_index
                        elif column in numeric_columns:
                            interpolated_row[column] = df.loc[i - 1, column] + (
                                (df.loc[i, column] - df.loc[i - 1, column]) / (missing_frames + 1)) * j
                        else:
                            interpolated_row[column] = df.loc[i - 1, column]

                    print(f"Filling missing frame index: {new_frame_index}")
                    new_rows.append(interpolated_row)

        # Add interpolated rows to the DataFrame
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

        # Sort the DataFrame by 'frameIndex'
        df.sort_values(by=['frameIndex'], inplace=True)

        # Save the DataFrame to CSV with the same name as the JSON file
        csv_path = os.path.splitext(json_path)[0] + '.csv'
        df.to_csv(csv_path, index=False)
        
        print(json.dumps({'csv_path': csv_path, 'total_entries': total_entries}))
        sys.exit(0)

    except Exception as e:
        print(f"Exception occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: create_csv_from_json.py <json_path>", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]
    create_csv_from_json(json_path)
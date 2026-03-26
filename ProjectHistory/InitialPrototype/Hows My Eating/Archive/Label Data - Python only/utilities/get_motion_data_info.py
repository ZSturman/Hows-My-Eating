import sys
import json

def calculate_total_duration(file_path):
    try:
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract timestamps and calculate the total duration
        if not data:
            print("Error: The JSON file is empty.")
            return None
        
        # Extract the first and last timestamps
        start_time = data[0]['timestamp']
        end_time = data[-1]['timestamp']
        total_duration = end_time - start_time

        return {
            'duration': total_duration
        }

    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: calculate_total_duration.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    duration = calculate_total_duration(file_path)

    if duration is not None:
        print(json.dumps(duration))
    else:
        print("Failed to calculate total duration.")
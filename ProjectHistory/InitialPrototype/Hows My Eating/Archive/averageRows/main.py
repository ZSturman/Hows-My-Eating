import os
import pandas as pd

def calculate_average_rows(folder_path: str) -> float:
    """
    Calculates the average number of rows in all CSV files within the given folder.

    :param folder_path: Path to the folder containing the CSV files.
    :return: The average number of rows across all CSV files.
    """
    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    
    if not csv_files:
        raise ValueError("No CSV files found in the specified folder.")

    total_rows = 0
    file_count = len(csv_files)

    for csv_file in csv_files:
        file_path = os.path.join(folder_path, csv_file)
        try:
            df = pd.read_csv(file_path)
            total_rows += len(df)
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    return total_rows / file_count

# Example usage
if __name__ == "__main__":
    folder_path = "/Users/zacharysturman/Desktop/myData/data_start_end/data_start_end_1/chew"
    try:
        avg_rows = calculate_average_rows(folder_path)
        print(f"The average number of rows across all CSV files is: {avg_rows:.2f}")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")
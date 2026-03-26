import csv
import os
from typing import Dict, Optional, Union
import pandas as pd
import traceback

def safe_divide(numerator, denominator, logger):
    try:
        return numerator / denominator if denominator != 0 else None
    except Exception as e:
        logger.error(f"safe_divide error: {e}, numerator={numerator}, denominator={denominator}")
        return None


def calculate_ratios(input_csv: str, output_csv: str, logger):
    try: 
        # Read input CSV
        df = pd.read_csv(input_csv)
        logger.info(f"Processing ratios from {input_csv}, total rows: {len(df)}")

        # Define column names as a dictionary
        cols = {
            "mouth_width": "p49_p55",
            "top_lip_height": "p52_p63",
            "bottom_lip_height": "p67_p58",
            "between_lips": "p63_p67",
            "nose_to_lips": "p34_p52",
            "lips_to_chin": "p58_p9",
        }

        # Output column names
        output_cols = [
            "frame",
            "timestamp",
            "feat_nose_to_lips_lips_to_chin",
            "feat_between_lips_to_mouth_width",
            "feat_top_lip_height_to_mouth_width",
            "feat_bottom_lip_height_to_mouth_width",
            "feat_mouth_width_nose_to_chin",
            "feat_mouth_width_outside_lips",
            "feat_mouth_width_inside_lips",
        ]

        with open(output_csv, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=output_cols)
            writer.writeheader()

            for idx, row in df.iterrows():
                try:
                    # Compute repetitive terms once
                    top_lip_height = row[cols["top_lip_height"]]
                    bottom_lip_height = row[cols["bottom_lip_height"]]
                    between_lips = row[cols["between_lips"]]
                    nose_to_lips = row[cols["nose_to_lips"]]
                    lips_to_chin = row[cols["lips_to_chin"]]
                    mouth_width = row[cols["mouth_width"]]

                    # Safe ratios
                    total_vertical = top_lip_height + bottom_lip_height + between_lips + nose_to_lips + lips_to_chin
                    ratios = {
                        "frame": row["frame"],
                        "timestamp": row["timestamp"],
                        "feat_nose_to_lips_lips_to_chin": safe_divide(nose_to_lips, lips_to_chin, logger),
                        "feat_between_lips_to_mouth_width": safe_divide(between_lips, mouth_width, logger),
                        "feat_top_lip_height_to_mouth_width": safe_divide(top_lip_height, mouth_width, logger),
                        "feat_bottom_lip_height_to_mouth_width": safe_divide(bottom_lip_height, mouth_width, logger),
                        "feat_mouth_width_nose_to_chin": safe_divide(mouth_width, total_vertical, logger),
                        "feat_mouth_width_outside_lips": safe_divide(mouth_width, total_vertical, logger),
                        "feat_mouth_width_inside_lips": safe_divide(mouth_width, between_lips, logger),
                    }

                    writer.writerow(ratios)
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}", exc_info=True)
                    
        logger.info(f"Ratios calculated and saved to {output_csv}")
        return output_csv
    except Exception as e:
        logger.error(f"Failed to calculate ratios: {e}\n{traceback.format_exc()}")
        return None



def compare_visuals(input_csv_file_path: str, compare_csv_file_name: str, logger) -> Union[Dict[str, Optional[Union[Dict, str]]], str]:
    """
    Handles the video processing pipeline, extracting and analyzing data from a .mov file.

    Args:
        collected_data_path (str): Path to the directory containing the video.
        output_video (bool): Whether to generate a processed output video.
        logger: Logger instance.

    Returns:
        Union[Dict[str, Optional[Union[Dict, str]]], str]:
            A dictionary containing processed data and file paths, or an error message.
    """
    try:
        
        # Pop off the last element of the input_csv_file_path to get the directory
        collected_data_path = os.path.dirname(input_csv_file_path)
        output_csv_path_2 = os.path.join(collected_data_path, f"{compare_csv_file_name}.csv")
        
        result_file = calculate_ratios(input_csv_file_path, output_csv_path_2, logger)
        
        if result_file:
            return {"csv_file": output_csv_path_2 }
    except Exception as e:
        logger.error(f"An error occurred during the processing: {e}", exc_info=True)
        return f"An error occurred during the processing: {e}"
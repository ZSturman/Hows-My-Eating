import argparse
from pipeline.export_handler import export_file_handler
from utils.logging import setup_logging
from utils.formatter import json_response

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split video into bite and chew events based on a merged CSV label file."
    )
    parser.add_argument(
        "output_folder_dir",
        type=str,
        help="Path to the directory containing the video and labelled data."
    )
    parser.add_argument(
        "motion_data_file",
        type=str,
        help="Path to the JSON file containing motion data."
    )
    parser.add_argument(
        "mov_info_file",
        type=str,
        help="Path to the JSON file containing movie metadata."
    )
    parser.add_argument(
        "ratios_data_file",
        type=str,
        help="Path to the CSV file containing ratios data."
    )
    parser.add_argument(
        "pointsdata_file",
        type=str,
        help="Path to the CSV file containing points data."
    )
    parser.add_argument(
        "merged_data_file",
        type=str,
        help="Path to the CSV file containing merged data."
    )
    parser.add_argument(
        "chunks_dir",
        type=str,
        help="Directory to save the video chunks."
    )
    parser.add_argument(
        "chunks_records",
        type=str,
        help="Path to the CSV file containing the chunks records."
    )
    parser.add_argument("--log_file", type=str, help="Path to the log file.", default="exporting.log")

    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging(args.log_file)

    try:
        output_folder_dir = args.output_folder_dir
        motion_data_file = args.motion_data_file
        mov_info_file = args.mov_info_file
        ratios_data_file = args.ratios_data_file
        points_data_file = args.pointsdata_file
        merged_data_file = args.merged_data_file
        chunks_dir = args.chunks_dir
        chunks_records = args.chunks_records
        

        # Extract events from the CSV
        result = export_file_handler(
            output_folder_dir, motion_data_file, mov_info_file, ratios_data_file, points_data_file, merged_data_file, chunks_dir, chunks_records, logger
        )
        

        if result:
            logger.info(f"Successfully created {len(result)} video chunks.")
            return json_response(True, "Video chunks created successfully.", {"chunks": result})
        else:
            logger.error("Failed to create video chunks.")
            return json_response(False, "Failed to create video chunks.", {"error": "No chunks generated."})

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return json_response(False, "An unexpected error occurred.", {"error": str(e)})


if __name__ == "__main__":
    main()
import argparse
from pipeline.labels_to_csv import merge_labels
from utils.formatter import json_response
from utils.logging import setup_logging

def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Merge labelled data with video metadata and save as CSV."
    )
    parser.add_argument(
        "dir_path",
        type=str,
        help="Path to the directory containing the video and labelled data."
    )
    parser.add_argument(
        "labelled_json_filepath",
        type=str,
        help="Path to the labelled data JSON file."
    )
    parser.add_argument(
        "mov_info_file_path",
        type=str,
        help="Path to the mov_info JSON file."
    )
    parser.add_argument(
        "merged_csv_output_name",
        type=str,
        help="The base name for the merged CSV output file (without extension)."
    )
    parser.add_argument(
        "--log_file",
        type=str,
        help="Path to the log file.",
        default="merge.txt"
    )
    return parser.parse_args()

def main():
    """Main entry point for merging labelled data with video metadata."""
    args = parse_args()
    logger = setup_logging(args.log_file)

    try:
        dir_path: str = args.dir_path
        labelled_json_filepath: str = args.labelled_json_filepath
        mov_info_file_path: str = args.mov_info_file_path
        merged_csv_output_name: str = args.merged_csv_output_name

        logger.info(f"Merging started for {labelled_json_filepath}")

        result = merge_labels(dir_path, labelled_json_filepath, mov_info_file_path, merged_csv_output_name, logger)

        if result:
            logger.info(f"Merging completed successfully. Output file: {result}")
            json_response(True, "Merge completed successfully.", {"merged_csv": result})
        else:
            logger.error("Merge failed. merge_labels returned None.")
            json_response(False, "Merge failed.", {"error": "merge_labels returned None"})

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        json_response(False, "An unexpected error occurred.", {"error": str(e)})

if __name__ == "__main__":
    main()
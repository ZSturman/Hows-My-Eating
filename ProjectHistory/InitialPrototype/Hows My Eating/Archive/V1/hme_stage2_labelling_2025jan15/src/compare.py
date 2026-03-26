
import argparse
from src.pipeline.compare import compare_visuals
from utils.formatter import json_response
from utils.logging import setup_logging

def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract and save video metadata.")
    parser.add_argument("input_csv_file_path", type=str, help="Path to the .json and .mov files.")
    parser.add_argument("compare_csv_file_name" , type=str, help="Name of the compare visuals file.")
    parser.add_argument("--log_file", type=str, help="Path to the log file.", default="step1_log.txt")
    return parser.parse_args()


def main():
    """Main entry point for processing video metadata."""
    args = parse_args()
    logger = setup_logging(args.log_file)

    try:
        input_csv_file_path: str = args.input_csv_file_path
        compare_csv_file_name: str = args.compare_csv_file_name
        
        logger.info(f"Comparing started for {input_csv_file_path}")

        result = compare_visuals(input_csv_file_path, compare_csv_file_name, logger)
        logger.info(f"Comparing completed. Results: {result}")

        # Ensure result is a dictionary before responding
        if isinstance(result, dict):
            json_response(True, "Ratio creation completed successfully.", result)
        else:
            json_response(False, "Unexpected error: result is not a dictionary.", {"error": str(result)})

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        json_response(False, "An unexpected error occurred.", {"error": str(e)})

if __name__ == "__main__":
    main()
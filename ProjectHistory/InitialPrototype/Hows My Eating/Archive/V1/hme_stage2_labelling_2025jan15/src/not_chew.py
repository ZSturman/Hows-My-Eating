
import argparse
from pipeline.not_chew import export_not_chews
from utils.formatter import json_response
from utils.logging import setup_logging

def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract and save video metadata.")
    parser.add_argument("collected_data_path", type=str, help="Path to the .json files.")
    parser.add_argument("output_dir", type=str, help="Directory to save the video chunks.")
    parser.add_argument("--log_file", type=str, help="Path to the log file.", default="not-chews.log")
    return parser.parse_args()


def main():
    """Main entry point for processing video metadata."""
    args = parse_args()
    logger = setup_logging(args.log_file)
    
    try:
        collected_data_path = args.collected_data_path
        output_dir = args.output_dir
        logger.info(f"Processing started for {collected_data_path}")

        result = export_not_chews(collected_data_path, output_dir, logger)
        logger.info(f"Processing completed. Results: {result}")

        # Ensure result is a dictionary before responding
        if isinstance(result, dict):
            json_response(True, "Not Chews completed successfully.", result)
        else:
            json_response(False, "Unexpected error: result is not a dictionary.", {"error": str(result)})

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        json_response(False, "An unexpected error occurred.", {"error": str(e)})

if __name__ == "__main__":
    main()
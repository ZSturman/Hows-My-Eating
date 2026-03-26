import argparse
from pipeline.process import process_visuals
from utils.formatter import json_response
from utils.logging import setup_logging

def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract and save video metadata.")
    parser.add_argument("collected_data_path", type=str, help="Path to the .json and .mov files.")
    parser.add_argument("processed_visuals_file_name" , type=str, help="Name of the processed visuals file.")
    parser.add_argument("--log_file", type=str, help="Path to the log file.", default="step1_log.txt")
    parser.add_argument("--output-video", type=bool, help="Output video path.", default=True)
    return parser.parse_args()


def main():
    """Main entry point for processing video metadata."""
    args = parse_args()
    logger = setup_logging(args.log_file)

    try:
        collected_data_path: str = args.collected_data_path
        output_video: bool = args.output_video
        processed_visuals_file_name: str = args.processed_visuals_file_name
        logger.info(f"Processing started for {collected_data_path}. Will output video: {output_video}")

        result = process_visuals(collected_data_path, processed_visuals_file_name, output_video, logger)
        logger.info(f"Processing completed. Results: {result}")

        # Ensure result is a dictionary before responding
        if isinstance(result, dict):
            json_response(True, "Process Visuals completed successfully.", result)
        else:
            json_response(False, "Unexpected error: result is not a dictionary.", {"error": str(result)})

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        json_response(False, "An unexpected error occurred.", {"error": str(e)})

if __name__ == "__main__":
    main()
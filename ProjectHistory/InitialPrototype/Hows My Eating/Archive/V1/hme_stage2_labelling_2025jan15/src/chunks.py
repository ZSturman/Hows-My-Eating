import argparse
from pipeline.split_video_by_events import extract_events, create_mov_chunks
from utils.logging import setup_logging
from utils.formatter import json_response

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split video into bite and chew events based on a merged CSV label file."
    )
    parser.add_argument(
        "video_clip",
        type=str,
        help="Path to the video file (should have the same number of frames as the labels)."
    )
    parser.add_argument(
        "labels",
        type=str,
        help="Path to the CSV file containing the merged labels."
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory to save the video chunks."
    )
    parser.add_argument("--log_file", type=str, help="Path to the log file.", default="chunks.txt")

    return parser.parse_args()


def main():
    args = parse_args()
    logger = setup_logging(args.log_file)

    try:
        video_clip = args.video_clip
        labels = args.labels
        output_dir = args.output_dir

        logger.info(f"Starting video processing for: {video_clip}")
        logger.info(f"Using labels from: {labels}")
        logger.info(f"Output directory: {output_dir}")

        # Extract events from the CSV
        events = extract_events(labels, logger)
        if not events:
            logger.error("No valid events found in the CSV file.")
            return json_response(False, "No valid events found in the CSV file.", {"error": "No events found."})

        # Create video chunks from events
        result = create_mov_chunks(events, video_clip, output_dir, logger)

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
import json
import subprocess
from typing import Dict, Union

def get_mov_info(file_path: str, logger) -> Union[Dict[str, Union[str, float, int]], None]:
    """
    Retrieves metadata from a video file using ffprobe.

    Parameters:
        file_path (str): Path to the video file.
        logger: Logger instance for logging messages.

    Returns:
        dict: A dictionary containing video metadata, including duration, width, height, FPS, and total frames.
        None: If an error occurs.
    """
    try:
        # Execute ffprobe command to get video metadata
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check for errors in execution
        if result.returncode != 0:
            logger.error(f"FFprobe Error: {result.stderr.strip()}")
            return None

        # Parse JSON output from ffprobe
        info = json.loads(result.stdout)

        # Validate extracted data
        if 'format' not in info or 'streams' not in info or not info['streams']:
            logger.error("Invalid or missing metadata from ffprobe output.")
            return None

        # Extract duration
        duration = float(info['format'].get('duration', 0.0))

        # Extract width and height
        width = int(info['streams'][0].get('width', 0))
        height = int(info['streams'][0].get('height', 0))

        # Calculate FPS from r_frame_rate
        fps_str = info['streams'][0].get('r_frame_rate', '0/1')
        try:
            num, denom = map(int, fps_str.split('/'))
            fps = num / denom if denom != 0 else 0
        except ValueError:
            logger.error("Invalid frame rate format.")
            return None

        # Calculate total frames
        total_frames = int(duration * fps)

        metadata = {
            'video_path': file_path,
            'duration': duration,
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': total_frames
        }
        
        logger.info(f"Extracted video metadata: {metadata}")
        return metadata

    except json.JSONDecodeError:
        logger.error("Error decoding JSON output from ffprobe.")
    except FileNotFoundError:
        logger.error("FFprobe not found. Ensure it is installed and in the system path.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    
    return None


""" 

ADD METADATA TO VIDEO FILE

import ffmpeg
import json

def add_bulk_metadata(input_file: str, metadata_file: str, output_file: str):
    # Read metadata from the JSON file
    with open(metadata_file, 'r') as file:
        metadata = json.load(file)

    # Extract general metadata and timestamps
    general_metadata = metadata.get("custom_tags", {})
    timestamps = metadata.get("timestamps", [])

    # Add general metadata
    ffmpeg_metadata = {f"metadata:{key}": value for key, value in general_metadata.items()}

    # Create a chapters file for FFmpeg
    chapter_lines = []
    for idx, ts in enumerate(timestamps):
        start = ts["start"]
        end = ts["end"]
        label = ts["label"]
        chapter_lines.append(f"[CHAPTER]\nTIMEBASE=1/1\nSTART={convert_to_seconds(start)}\nEND={convert_to_seconds(end)}\ntitle={label}\n")

    # Write chapters to a temporary file
    chapters_file = "chapters.txt"
    with open(chapters_file, "w") as f:
        f.writelines(chapter_lines)

    # Add metadata and chapters to the file
    (
        ffmpeg
        .input(input_file)
        .output(output_file, **ffmpeg_metadata, map_metadata="-1", ffmetadata=chapters_file)
        .run(overwrite_output=True)
    )

    print(f"Metadata and chapters added to {output_file}")


def convert_to_seconds(timestamp: str) -> int:
    # Convert a timestamp (HH:MM:SS) to seconds.
    h, m, s = map(int, timestamp.split(":"))
    return h * 3600 + m * 60 + s


# Example usage
input_mp4 = "input.mp4"
metadata_json = "metadata.json"
output_mp4 = "output_with_metadata.mp4"

add_bulk_metadata(input_mp4, metadata_json, output_mp4) 


import ffmpeg

def extract_mp3_with_metadata(input_mp4: str, output_mp3: str):

    # Extracts an MP3 file from an MP4 file while preserving metadata.

    try:
        # Extract MP3 audio while preserving metadata
        (
            ffmpeg
            .input(input_mp4)
            .output(output_mp3, codec="libmp3lame", qscale:a=2, map_metadata=0)
            .run(overwrite_output=True)
        )
        print(f"MP3 extracted and saved to {output_mp3}")
    except ffmpeg.Error as e:
        print("An error occurred during the conversion process:")
        print(e)

# Example usage
input_file = "input.mp4"
output_file = "output.mp3"
extract_mp3_with_metadata(input_file, output_file)









"""

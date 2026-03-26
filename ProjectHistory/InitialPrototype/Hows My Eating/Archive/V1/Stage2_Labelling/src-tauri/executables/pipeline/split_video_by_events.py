import os
import pandas as pd
from moviepy import VideoFileClip
from typing import List, Dict, Optional


def extract_events(labels_csv: str, logger) -> List[Dict[str, int]]:
    """
    Extracts events from a CSV file based on bite and chew transitions.
    
    A valid event starts when the mouth transitions from "Closed" to "Open"
    (with the action being either "Bite" or "Chew") and ends when the mouth
    transitions back from "Open" to "Closed".

    Args:
        labels_csv (str): Path to the CSV file containing labeled frames.
        logger: Logger instance for logging messages.

    Returns:
        List[Dict[str, int]]: A list of event dictionaries containing:
            - "type": either "Bite" or "Chew"
            - "start_frame": starting frame number
            - "end_frame": ending frame number
    """
    try:
        logger.info(f"Reading CSV file: {labels_csv}")
        df = pd.read_csv(labels_csv)

        if df.empty:
            logger.warning("CSV file is empty. No events to extract.")
            return []

        # Ensure the CSV is sorted by frame
        df = df.sort_values(by="frame").reset_index(drop=True)

        events = []
        n = len(df)
        i = 0

        while i < n - 1:
            current_mouth = str(df.at[i, 'mouth']).strip().lower()
            next_mouth = str(df.at[i + 1, 'mouth']).strip().lower()

            if current_mouth == "closed" and next_mouth == "open":
                event_type = df.at[i + 1, 'action'].strip()

                if event_type not in ("Bite", "Chew"):
                    i += 1
                    continue

                start_frame = df.at[i, 'frame']
                j = i + 1
                found_end = False

                while j < n - 1:
                    current_state = str(df.at[j, 'mouth']).strip().lower()
                    next_state = str(df.at[j + 1, 'mouth']).strip().lower()

                    if current_state == "open" and next_state == "closed":
                        end_frame = df.at[j + 1, 'frame']
                        found_end = True
                        break

                    j += 1

                if found_end:
                    events.append({
                        "type": event_type,
                        "start_frame": start_frame,
                        "end_frame": end_frame
                    })
                    logger.info(f"Extracted event: {event_type} ({start_frame} -> {end_frame})")
                    i = j + 1
                else:
                    logger.warning("No valid closing transition found for an event.")
                    break
            else:
                i += 1

        if not events:
            logger.warning("No valid events found in the CSV file.")
        else:
            logger.info(f"Extracted {len(events)} events from CSV.")

        return events

    except Exception as e:
        logger.error(f"Error extracting events from CSV: {e}", exc_info=True)
        return []


def create_mov_chunks(events: List[Dict[str, int]], video_path: str, output_dir: str, logger) -> Optional[List[str]]:
    """
    Creates video chunks based on detected events.

    Args:
        events (List[Dict[str, int]]): List of extracted events.
        video_path (str): Path to the input video file.
        output_dir (str): Directory to save the video chunks.
        logger: Logger instance.

    Returns:
        Optional[List[str]]: List of paths to the saved video chunks, or None if an error occurs.
    """
    try:
        if not events:
            logger.warning("No events provided for video chunk creation.")
            return None

        logger.info(f"Loading video file: {video_path}")
        video_clip = VideoFileClip(video_path)
        fps = video_clip.fps

        os.makedirs(output_dir, exist_ok=True)

        output_files = []
        metadata_records = []
        bite_counter = 1
        chew_counter = 1

        for event in events:
            start_frame = event["start_frame"]
            end_frame = event["end_frame"]

            start_time = (start_frame - 1) / fps
            end_time = end_frame / fps

            try:
                event_clip = video_clip.subclipped(start_time, end_time)

                if event["type"] == "Bite":
                    out_filename = os.path.join(output_dir, f"bite{bite_counter}_start_frame{start_frame}_end_frame{end_frame}.mp4")
                    bite_counter += 1
                elif event["type"] == "Chew":
                    out_filename = os.path.join(output_dir, f"chew{chew_counter}_start_frame{start_frame}_end_frame{end_frame}.mp4")
                    chew_counter += 1
                else:
                    logger.warning(f"Unexpected event type encountered: {event['type']}")
                    continue

                logger.info(f"Saving event clip: {out_filename} ({start_time:.2f}s -> {end_time:.2f}s)")

                event_clip.write_videofile(
                    out_filename, 
                    codec="libx264", 
                    audio_codec="aac", 
                    ffmpeg_params=['-aspect', '9:16']
                )

                output_files.append(out_filename)
                
                metadata_records.append({
                    "type": event["type"],
                    "start_frame": start_frame,
                    "end_frame": end_frame,
                    "start_time": round(start_time, 3),
                    "end_time": round(end_time, 3),
                    "file_path": out_filename
                })

            except Exception as e:
                logger.error(f"Failed to process event {event}: {e}", exc_info=True)
                continue

        if output_files:
            logger.info(f"Successfully created {len(output_files)} video chunks.")
        else:
            logger.warning("No video chunks were successfully created.")
            
        # Save metadata as CSV and JSON
        if metadata_records:
            metadata_df = pd.DataFrame(metadata_records)

            csv_path = os.path.join(output_dir, "records.csv")

            metadata_df.to_csv(csv_path, index=False)

            logger.info(f"Metadata saved to: {csv_path}")

        return output_files if output_files else None

    except Exception as e:
        logger.error(f"Error during video chunk creation: {e}", exc_info=True)
        return None
import datetime
import json
import os
from typing import Dict, Optional, Tuple, Union
from ..utils.files import get_mov_from_dir
from ..utils.video_audio import get_mov_info
import cv2

def generate_video_thumbnails_for_scrubbing(video_path: str, output_dir: str, logger, num_thumbnails: int = 60, main_thumb_quality: int = 90, scrub_thumb_quality: int = 50) -> dict:
    """
    Extracts a fixed number of evenly spaced frames from the video for scrubbing, optimizing quality while maintaining the original aspect ratio.

    Args:
        video_path (str): Path to the video file.
        output_dir (str): Directory to save the thumbnails.
        logger: Logger instance.
        num_thumbnails (int): The number of thumbnails to generate.
        main_thumb_quality (int): JPEG quality for the first (main) thumbnail.
        scrub_thumb_quality (int): JPEG quality for all other thumbnails.

    Returns:
        dict: Dictionary containing paths for the main thumbnail and all scrubbing thumbnails.
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {}

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        logger.info(f"Video duration: {duration:.2f} seconds, FPS: {fps:.2f}")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        thumbnail_paths = []
        main_thumbnail_path = None

        if duration < num_thumbnails:
            logger.warning(f"Video duration is less than the number of thumbnails. Adjusting to {int(duration)} thumbnails.")
            num_thumbnails = int(duration)

        # Get evenly spaced timestamps
        timestamps = [duration * (i / (num_thumbnails - 1)) for i in range(num_thumbnails)]

        for i, time_pos in enumerate(timestamps):
            frame_position = int(fps * time_pos)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)

            success, frame = cap.read()
            if not success:
                logger.error(f"Failed to extract frame at {time_pos:.2f} sec.")
                continue

            # Define the thumbnail path
            output_thumb_path = os.path.join(output_dir, f"thumb_{i+1}.jpg")

            # Save the first frame with higher quality for the main thumbnail
            if i == 0:
                cv2.imwrite(output_thumb_path, frame, [cv2.IMWRITE_JPEG_QUALITY, main_thumb_quality])
                main_thumbnail_path = output_thumb_path
            else:
                cv2.imwrite(output_thumb_path, frame, [cv2.IMWRITE_JPEG_QUALITY, scrub_thumb_quality])

            thumbnail_paths.append(output_thumb_path)

        cap.release()
        logger.info(f"Generated {len(thumbnail_paths)} thumbnails. Main thumbnail saved at {main_thumbnail_path}.")
        return main_thumbnail_path, thumbnail_paths
    except Exception as e:
        logger.error(f"Failed to generate thumbnails: {e}", exc_info=True)
        return {}

def get_and_save_mov_info(video_path: str, output_json_path: str, logger) -> Optional[Tuple[Dict, str]]:
    """
    Extracts video metadata and saves it to a JSON file.

    Args:
        video_path (str): Path to the video file.
        output_json_path (str): Path where the JSON file should be saved.
        logger: Logger instance.

    Returns:
        Optional[Tuple[Dict, str]]: A tuple containing the video metadata and the path to the saved JSON file,
                                    or None if an error occurs.
    """
    try:
        mov_info = get_mov_info(video_path, logger)
        if not mov_info:
            logger.error(f"Failed to retrieve metadata for {video_path}")
            return None

        logger.info(f"Video info: {mov_info}")

        with open(output_json_path, "w") as json_file:
            json.dump(mov_info, json_file, indent=4)

        logger.info(f"Video info saved to {output_json_path}")
        return mov_info, output_json_path
    except Exception as e:
        logger.error(f"Failed to get and save video info: {e}", exc_info=True)
        return None



       
def collect_mov_info(collected_data_path: str, mov_info_file_name:str, logger) -> Union[Dict[str, Optional[Union[Dict, str]]], str]:
    """
    Processes video to extract metadata and save it as a JSON file.

    Args:
        collected_data_path (str): Path to the directory containing the video.
        logger: Logger instance.

    Returns:
        Union[Dict[str, Optional[Union[Dict, str]]], str]: A dictionary containing the JSON file path and metadata,
                                                           or an error message if something goes wrong.
    """
    try:
        video_path = get_mov_from_dir(collected_data_path)
        if not video_path:
            raise FileNotFoundError(
                f"No matching .mov file found in the directory '{collected_data_path}'. Ensure the file name matches the directory name."
            )

        # Define output path
        output_mov_info_path = os.path.join(collected_data_path, f"{mov_info_file_name}.json")

        # Extract and save movie info
        mov_info_result = get_and_save_mov_info(video_path, output_mov_info_path, logger)
        
        if not mov_info_result:
            logger.error("Failed to retrieve and save video metadata.")
            return "Failed to retrieve and save video metadata."
    
        mov_info, mov_info_file_path = mov_info_result
        
        
        
        """ output_thumb_dir = os.path.join(collected_data_path, "thumbnails")
        os.makedirs(output_thumb_dir, exist_ok=True)
        main_thumbnail_path, thumbnail_paths = generate_video_thumbnails_for_scrubbing(
            video_path,
            output_thumb_dir,
            logger,
        )
        
        if not main_thumbnail_path:
            logger.error("Failed to generate video main_thumbnail_path.")
            main_thumbnail_path = ""
            
        if not thumbnail_paths:
            logger.error("Failed to generate video thumbnail_paths.")
            thumbnail_paths = [] """

        # Return structured results
        result: Dict[str, Optional[Union[Dict, str]]] = {
            "mov_info": mov_info,
            "mov_info_file_path": mov_info_file_path,
            #"main_thumbnail_path": main_thumbnail_path,
            #"scrubbing_thumbnails_paths": thumbnail_paths,
        }

        logger.info(f"Processing completed. Results: {result}")
        return result
    except Exception as e:
        logger.error(f"An error occurred during the processing of the video: {e}", exc_info=True)
        return f"An error occurred during the processing of the video: {e}"
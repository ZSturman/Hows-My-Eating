import subprocess
import sys
import json

def get_mov_info(file_path):
    try:
        # Execute ffprobe command to get duration, fps, width, and height
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

        # Check for errors
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
            return None

        # Parse the JSON output from ffprobe
        info = json.loads(result.stdout)

        # Extract duration
        duration = float(info['format']['duration'])

        # Extract width and height
        width = int(info['streams'][0]['width'])
        height = int(info['streams'][0]['height'])

        # Calculate FPS from r_frame_rate
        fps_str = info['streams'][0]['r_frame_rate']
        num, denom = map(int, fps_str.split('/'))
        fps = num / denom if denom != 0 else 0

        # Calculate the number of frames
        total_frames = int(duration * fps)

        return {
            'duration': duration,
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': total_frames
        }

    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: get_mov_info.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    info = get_mov_info(file_path)

    if info is not None:
        print(json.dumps(info))
    else:
        print("Failed to get file information.")
import subprocess
import sys
import json
import os

def extract_audio(file_path):
    try:
        # Generate output file path for the .wav file
        output_wav_path = os.path.splitext(file_path)[0] + ".wav"

        # Use ffmpeg to extract audio from the .mov file and save it as .wav
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", file_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", "44100",  # Sample rate
                "-ac", "2",  # Number of audio channels
                output_wav_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check for errors
        if result.returncode != 0:
            print(f"Error: {result.stderr.strip()}")
            return None

        # Use ffprobe to get audio file details
        audio_info_result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "stream=duration:stream=channels:stream=sample_rate",
                "-of", "json",
                output_wav_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check for errors in ffprobe
        if audio_info_result.returncode != 0:
            print(f"Error: {audio_info_result.stderr.strip()}")
            return None

        # Parse the JSON output from ffprobe
        audio_info = json.loads(audio_info_result.stdout)
        stream_info = audio_info['streams'][0] if 'streams' in audio_info and len(audio_info['streams']) > 0 else {}

        # Extract audio details
        duration = float(stream_info.get('duration', 0))
        channels = int(stream_info.get('channels', 0))
        sample_rate = int(stream_info.get('sample_rate', 0))

        return {
            'duration': duration,
            'channels': channels,
            'sample_rate': sample_rate,
            'output_path': output_wav_path
        }

    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_audio.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    audio_info = extract_audio(file_path)

    if audio_info is not None:
        print(json.dumps(audio_info))
    else:
        print("Failed to extract audio information.")
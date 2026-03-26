import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
from mutagen.wave import WAVE
import os

def get_audio_metadata(file_path):
    metadata = {}
    
    if not os.path.isfile(file_path):
        return {"error": "File not found"}
    
    try:
        if file_path.endswith('.m4a'):
            audio = MP4(file_path)
            tags = audio.tags if audio.tags else {}
            metadata = {
                "title": tags.get('\xa9nam', [None])[0],
                "artist": tags.get('\xa9ART', [None])[0],
                "album": tags.get('\xa9alb', [None])[0],
                "genre": tags.get('\xa9gen', [None])[0],
                "track_number": tags.get('trkn', [(None, None)])[0][0] if tags.get('trkn') else None,
                "year": tags.get('\xa9day', [None])[0],
                "comment": tags.get('\xa9cmt', [None])[0],
                "composer": tags.get('\xa9wrt', [None])[0],
                "album_artist": tags.get('aART', [None])[0],
                "disc_number": tags.get('disk', [(None, None)])[0][0] if tags.get('disk') else None,
                "bpm": tags.get('tmpo', [None])[0],
                "key": tags.get('©key', [None])[0],
                "duration": audio.info.length,
                "sample_rate": audio.info.sample_rate,
                "bit_rate": audio.info.bitrate,
                "file_size": os.path.getsize(file_path),
                "file_format": 'm4a',
                "channel_count": audio.info.channels,
                "bit_depth": None,
                "creation_date": os.path.getctime(file_path),
                "modification_date": os.path.getmtime(file_path),
                "location": None  # This would need to be manually added if available
            }
        elif file_path.endswith('.wav'):
            audio = WAVE(file_path)
            metadata = {
                "title": None,
                "artist": None,
                "album": None,
                "genre": None,
                "track_number": None,
                "year": None,
                "comment": None,
                "composer": None,
                "album_artist": None,
                "disc_number": None,
                "bpm": None,
                "key": None,
                "duration": audio.info.length,
                "sample_rate": audio.info.sample_rate,
                "bit_rate": None,
                "file_size": os.path.getsize(file_path),
                "file_format": 'wav',
                "channel_count": audio.info.channels,
                "bit_depth": audio.info.bits_per_sample,
                "creation_date": os.path.getctime(file_path),
                "modification_date": os.path.getmtime(file_path),
                "location": None  # This would need to be manually added if available
            }
        else:
            return {"error": "Unsupported file format"}
    except Exception as e:
        return {"error": str(e)}
    
    return metadata



# Example usage:
wav_file_path = 'data/2024-07-01_14-22-34/audio_data_2024-07-01_14-22-34.wav'
m4a_file_path = 'data/2024-07-01_14-22-34/audio_data_2024-07-01_14-22-34.m4a'
wav_metadata = get_audio_metadata(wav_file_path)
m4a_metadata = get_audio_metadata(m4a_file_path)

print("WAV", wav_metadata)
print("M4A", m4a_metadata)

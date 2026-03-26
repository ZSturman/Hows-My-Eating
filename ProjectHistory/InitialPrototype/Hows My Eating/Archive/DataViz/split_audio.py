from pydub import AudioSegment
import json
import os

def split_audio(audio_file, chunk_length=1000):
    audio = AudioSegment.from_file(audio_file)
    chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
    return chunks

def split_json(json_data, chunk_length=1.0):
    chunks = {}
    for entry in json_data:
        time_index = int(entry['timestamp'] // chunk_length)
        if time_index not in chunks:
            chunks[time_index] = []
        # Adjust the timestamp
        entry['timestamp'] -= time_index * chunk_length
        chunks[time_index].append(entry)
    return chunks

def save_audio_chunks(audio_chunks, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i, chunk in enumerate(audio_chunks):
        chunk.export(os.path.join(output_dir, f'audio_chunk_{i+1}.wav'), format="wav")

def save_json_chunks(json_chunks, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i in sorted(json_chunks.keys()):
        with open(os.path.join(output_dir, f'json_chunk_{i+1}.json'), 'w') as f:
            json.dump(json_chunks[i], f, indent=4)

def main(audio_file, json_file, output_dir):
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    audio_chunks = split_audio(audio_file)
    json_chunks = split_json(json_data)
    
    save_audio_chunks(audio_chunks, os.path.join(output_dir, 'audio'))
    save_json_chunks(json_chunks, os.path.join(output_dir, 'json'))

if __name__ == "__main__":
    audio_file = "data_split/2024-07-03_15-01-37/audio_data_2024-07-03_15-01-37.wav"
    json_file = 'data_split/2024-07-03_15-01-37/motion_data_2024-07-03_15-01-37.json'
    output_dir = 'output_directory'
    
    main(audio_file, json_file, output_dir)
    
    
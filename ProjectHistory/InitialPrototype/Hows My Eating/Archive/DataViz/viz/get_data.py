import wave
import json
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# Load JSON file
json_file_path = './data/2024-07-03_15-37-54/motion_data_2024-07-03_15-37-54.json'
with open(json_file_path, 'r') as f:
    motion_data = json.load(f)

# Calculate duration from JSON timestamps
timestamps = [entry["timestamp"] for entry in motion_data]
start_time = min(timestamps)
timestamps = [t - start_time for t in timestamps]
duration_json = max(timestamps)

# Load WAV file to get sample rate, number of frames, and number of channels
wav_file_path = './data/2024-07-03_15-37-54/audio_data_2024-07-03_15-37-54.wav'
with wave.open(wav_file_path, 'r') as wav_file:
    sample_rate_wav = wav_file.getframerate()
    n_frames_wav = wav_file.getnframes()
    n_channels = wav_file.getnchannels()
    duration_wav = n_frames_wav / float(sample_rate_wav)

print(f"JSON duration: {duration_json} seconds")
print(f"WAV duration: {duration_wav} seconds")
print(f"WAV file stats - Sample Rate: {sample_rate_wav}, Frames: {n_frames_wav}, Channels: {n_channels}")

# Load the actual audio data
with wave.open(wav_file_path, 'rb') as wav_file:
    audio_frames = wav_file.readframes(n_frames_wav)
    audio_samples = np.frombuffer(audio_frames, dtype=np.int16)

# Calculate the start frame index based on the start_time
start_frame_index = int(start_time * sample_rate_wav) * n_channels

# Trim the audio samples to start from the start_frame_index
audio_samples = audio_samples[start_frame_index:]

# Ensure the trimmed audio array size is divisible by the number of channels
n_samples = len(audio_samples) - (len(audio_samples) % n_channels)
audio_samples = audio_samples[:n_samples]

# Adjust the number of frames accordingly
n_frames_wav = len(audio_samples) // n_channels

# Reshape the audio samples to separate the channels properly
audio_samples = audio_samples.reshape(-1, n_channels)

# Select the first channel
audio_samples = audio_samples[:, 0]

# Update duration_wav after trimming
duration_wav = n_frames_wav / float(sample_rate_wav)

# Interpolate the audio samples
original_time_points = np.linspace(0, duration_wav, n_frames_wav)
interpolated_time_points = np.linspace(0, duration_json, int(duration_json * sample_rate_wav))
interpolator = interp1d(original_time_points, audio_samples, kind='linear', fill_value='extrapolate')
interpolated_audio_samples = interpolator(interpolated_time_points)

# Output interpolated audio samples to a new WAV file
output_wav_file_path = './data/2024-07-03_15-37-54/interpolated_audio_data_2024-07-03_15-37-54.wav'
with wave.open(output_wav_file_path, 'w') as output_wav_file:
    output_wav_file.setnchannels(1)
    output_wav_file.setsampwidth(2)  # 2 bytes for int16
    output_wav_file.setframerate(sample_rate_wav)
    output_wav_file.writeframes(interpolated_audio_samples.astype(np.int16).tobytes())

print(f"Interpolated audio samples: {len(interpolated_audio_samples)}")

# Plotting
plt.figure(figsize=(14, 8))

# Original audio samples
plt.subplot(2, 1, 1)
plt.plot(original_time_points, audio_samples, label='Original Audio Samples')
plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude')
plt.title('Original Audio Samples')
plt.legend()

# Interpolated audio samples
plt.subplot(2, 1, 2)
plt.plot(interpolated_time_points, interpolated_audio_samples, label='Interpolated Audio Samples', color='orange')
plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude')
plt.title('Interpolated Audio Samples')
plt.legend()

plt.tight_layout()
plt.show()



def plot_data_over_wav(df, wav_file):
    wav = wave.open(wav_file, 'r')
    
    # Extract audio parameters
    framerate, n_frames = wav.getframerate(), wav.getnframes()

    # Read audio data
    frames = wav.readframes(n_frames)
    audio_data = np.frombuffer(frames, dtype=np.int16)

    # Normalize audio data
    audio_data = audio_data / np.max(np.abs(audio_data))
    time_audio = np.linspace(0, n_frames / framerate, n_frames)

    # Plot settings
    sensor_data_columns = df.columns[1:]  # skip timestamp column

    for sensor in sensor_data_columns:
        fig, ax1 = plt.subplots(figsize=(10, 4))
        ax2 = ax1.twinx()
        
        ax1.plot(df['timestamp'], df[sensor], 'g-', label=f'{sensor}')
        ax2.plot(time_audio, audio_data, 'k-', alpha=0.5, label='Audio Waveform')
        
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel(sensor, color='g')
        ax2.set_ylabel('Normalized Audio Amplitude', color='k')
        
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
        plt.title(f'{sensor} and Audio Waveform Over Time')
        plt.show()
    
    wav.close()

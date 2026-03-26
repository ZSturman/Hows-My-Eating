import json
import pandas as pd
from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt
import wave

# Calculate the mean
# Calculate the variance

# Calculate the standard deviation

# Normalize the data


def create_df(json_path):
    # Load JSON data
    with open(json_path) as f:
        json_data = json.load(f)

    timestamps = [entry['timestamp'] for entry in json_data]
    user_accel = [entry['userAcceleration'] for entry in json_data]
    rotation_rate = [entry['rotationRate'] for entry in json_data]
    attitude = [entry['attitude'] for entry in json_data]

    user_accel_x = [entry['x'] for entry in user_accel]
    user_accel_y = [entry['y'] for entry in user_accel]
    user_accel_z = [entry['z'] for entry in user_accel]

    rotation_rate_x = [entry['x'] for entry in rotation_rate]
    rotation_rate_y = [entry['y'] for entry in rotation_rate]
    rotation_rate_z = [entry['z'] for entry in rotation_rate]

    attitude_roll = [entry['roll'] for entry in attitude]
    attitude_pitch = [entry['pitch'] for entry in attitude]
    attitude_yaw = [entry['yaw'] for entry in attitude]

    df = pd.DataFrame({
        'timestamp': timestamps,
        'user_accel_x': user_accel_x,
        'user_accel_y': user_accel_y,
        'user_accel_z': user_accel_z,
        'rotation_rate_x': rotation_rate_x,
        'rotation_rate_y': rotation_rate_y,
        'rotation_rate_z': rotation_rate_z,
        'attitude_roll': attitude_roll,
        'attitude_pitch': attitude_pitch,
        'attitude_yaw': attitude_yaw
    })

    return df




def plot_wav(wav_file):
    sample_rate, audio_data = wavfile.read(wav_file)
    print("Sample rate: ", sample_rate)
    print("Audio data: ", audio_data)
    
    # Generate timestamps
    time = np.linspace(0, len(audio_data) / sample_rate, num=len(audio_data))
    
    print("Time: ", time)
    

    plt.figure(figsize=(10, 3))
    plt.plot(time, audio_data)
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.title('Audio Signal')
    plt.show() 

    
    
    

def plot_data_over_wav(df, wav_file):
    wav = wave.open(wav_file, 'r')
    
    # Extract audio parameters
    n_channels, sampwidth, framerate, n_frames, comptype, compname = wav.getparams()
    duration = n_frames / framerate

    # Read audio data
    frames = wav.readframes(n_frames)
    audio_data = np.frombuffer(frames, dtype=np.int16)

    # Generate timestamps
    time_audio = np.linspace(0., duration, n_frames)
    
    # Normalize audio data
    audio_data = audio_data / np.max(np.abs(audio_data))
    
    # Normalize sensor data
    df['user_accel_x'] = df['user_accel_x'] / np.max(np.abs(df['user_accel_x']))
    df['user_accel_y'] = df['user_accel_y'] / np.max(np.abs(df['user_accel_y']))
    df['user_accel_z'] = df['user_accel_z'] / np.max(np.abs(df['user_accel_z']))
    
    df['rotation_rate_x'] = df['rotation_rate_x'] / np.max(np.abs(df['rotation_rate_x']))
    df['rotation_rate_y'] = df['rotation_rate_y'] / np.max(np.abs(df['rotation_rate_y']))
    df['rotation_rate_z'] = df['rotation_rate_z'] / np.max(np.abs(df['rotation_rate_z']))
    
    df['attitude_roll'] = df['attitude_roll'] / np.max(np.abs(df['attitude_roll']))
    df['attitude_pitch'] = df['attitude_pitch'] / np.max(np.abs(df['attitude_pitch']))
    df['attitude_yaw'] = df['attitude_yaw'] / np.max(np.abs(df['attitude_yaw']))
    
    # Plot sensor data
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['user_accel_x'], label='User Acceleration X')
    plt.plot(df['timestamp'], df['user_accel_y'], label='User Acceleration Y')
    plt.plot(df['timestamp'], df['user_accel_z'], label='User Acceleration Z')
    plt.plot(df['timestamp'], df['rotation_rate_x'], label='Rotation Rate X')
    plt.plot(df['timestamp'], df['rotation_rate_y'], label='Rotation Rate Y')
    plt.plot(df['timestamp'], df['rotation_rate_z'], label='Rotation Rate Z')
    plt.plot(df['timestamp'], df['attitude_roll'], label='Attitude Roll')
    plt.plot(df['timestamp'], df['attitude_pitch'], label='Attitude Pitch')
    plt.plot(df['timestamp'], df['attitude_yaw'], label='Attitude Yaw')
    
    plt.xlabel('Time [s]')
    plt.ylabel('Normalized Sensor Data')
    plt.title('Sensor Data')
    plt.legend()
    plt.show()
    
    # Plot audio data
    plt.figure(figsize=(10, 3))
    plt.plot(time_audio, audio_data)
    plt.xlabel('Time [s]')
    plt.ylabel('Normalized Audio Data')
    plt.title('Audio Data')
    
    plt.show()
    
    # Plot sensor data and audio data together
    fig, ax1 = plt.subplots()
    
    ax2 = ax1.twinx()
    ax1.plot(df['timestamp'], df['user_accel_x'], 'r-')
    ax1.plot(df['timestamp'], df['user_accel_y'], 'g-')
    ax1.plot(df['timestamp'], df['user_accel_z'], 'b-')
    ax2.plot(time_audio, audio_data, 'k-')
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('User Acceleration', color='r')
    ax2.set_ylabel('Audio', color='k')
    
    plt.show()
    
    return df

df = create_df('./data/2024-07-03_15-37-54/motion_data_2024-07-03_15-37-54.json')
plot_wav('./data/2024-07-03_15-37-54/interpolated_audio_data_2024-07-03_15-37-54.wav')
plot_data_over_wav(df, './data/2024-07-03_15-37-54/interpolated_audio_data_2024-07-03_15-37-54.wav')
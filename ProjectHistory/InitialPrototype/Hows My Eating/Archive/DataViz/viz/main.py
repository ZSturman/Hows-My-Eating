import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import wave

def create_df(json_path):
    # Load JSON data
    with open(json_path) as f:
        json_data = json.load(f)
        
    # Sort JSON data by timestamp
    json_data = sorted(json_data, key=lambda x: x['timestamp'])

    # Extract data from JSON
    timestamps = [entry['timestamp'] for entry in json_data]
    user_accel = [entry['userAcceleration'] for entry in json_data]
    rotation_rate = [entry['rotationRate'] for entry in json_data]
    attitude = [entry['attitude'] for entry in json_data]

    # Split sensor data into components
    user_accel_x = [entry['x'] for entry in user_accel]
    user_accel_y = [entry['y'] for entry in user_accel]
    user_accel_z = [entry['z'] for entry in user_accel]
    rotation_rate_x = [entry['x'] for entry in rotation_rate]
    rotation_rate_y = [entry['y'] for entry in rotation_rate]
    rotation_rate_z = [entry['z'] for entry in rotation_rate]
    attitude_roll = [entry['roll'] for entry in attitude]
    attitude_pitch = [entry['pitch'] for entry in attitude]
    attitude_yaw = [entry['yaw'] for entry in attitude]

    # Create DataFrame
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

    # Normalize timestamps to start from zero
    df['timestamp'] = df['timestamp'] - df['timestamp'].min()
    return df

# Paths and loading data
dir = './data/'
datetime = '2024-07-04_14-10-08'
json_path = dir + datetime + "/motion_data_" + datetime + ".json"
wav_file = dir + datetime + "/interpolated_audio_data_" + datetime + ".wav"

df = create_df(json_path)
#plot_data_over_wav(df, wav_file)

print(df.head())

df.to_csv(dir+datetime+"/"+datetime+"_data.csv", index=False)

# Plotting the data
plt.figure(figsize=(12, 8))

# Plot user acceleration
plt.subplot(2, 2, 1)
plt.plot(df['timestamp'], df['user_accel_x'], label='X')
plt.plot(df['timestamp'], df['user_accel_y'], label='Y')
plt.plot(df['timestamp'], df['user_accel_z'], label='Z')
plt.xlabel('Timestamp')
plt.ylabel('User Acceleration')
plt.title('User Acceleration')
plt.legend()

# Plot rotation rate
plt.subplot(2, 2, 2)
plt.plot(df['timestamp'], df['rotation_rate_x'], label='X')
plt.plot(df['timestamp'], df['rotation_rate_y'], label='Y')
plt.plot(df['timestamp'], df['rotation_rate_z'], label='Z')
plt.xlabel('Timestamp')
plt.ylabel('Rotation Rate')
plt.title('Rotation Rate')
plt.legend()

# Plot attitude
plt.subplot(2, 2, 3)
plt.plot(df['timestamp'], df['attitude_roll'], label='Roll')
plt.plot(df['timestamp'], df['attitude_pitch'], label='Pitch')
plt.plot(df['timestamp'], df['attitude_yaw'], label='Yaw')
plt.xlabel('Timestamp')
plt.ylabel('Attitude')
plt.title('Attitude')
plt.legend()

# Show the plot
plt.tight_layout()
plt.show()


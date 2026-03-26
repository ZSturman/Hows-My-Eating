import pandas as pd
from scipy.io import wavfile
import json
import numpy as np

def wav_to_dataframe(file_path):
    # Read the .wav file
    sample_rate, data = wavfile.read(file_path)
    
    # Check if the data has multiple channels (e.g., stereo)
    if len(data.shape) == 1:
        df = pd.DataFrame(data, columns=['amplitude'])
    else:
        num_channels = data.shape[1]
        columns = [f'amplitude_{i+1}' for i in range(num_channels)]
        df = pd.DataFrame(data, columns=columns)
    
    # Add a time column based on the sample rate
    df['timestamp'] = df.index / sample_rate
    
    return df, sample_rate


# Example usage
file_path = 'data/2024-07-03_15-37-54/audio_data_2024-07-03_15-37-54.wav' 
df, sample_rate = wav_to_dataframe(file_path)
print(df.head())



def json_to_dataframe(json_file_path):
    # Read JSON data from a file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Create a DataFrame
    df = pd.json_normalize(data)
    
    return df


# Convert JSON data to DataFrame
json_data = 'data/2024-07-03_15-37-54/motion_data_2024-07-03_15-37-54.json' 
json_df = json_to_dataframe(json_data)

print(json_df.head())


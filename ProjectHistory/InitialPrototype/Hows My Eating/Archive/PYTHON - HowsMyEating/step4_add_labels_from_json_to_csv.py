# step4.py
# Description: This script takes the labels from step5.json and fills in the missing frames using forward fill.
import csv
import json
import pandas as pd
import numpy as np

# Load step5.json
labels_json = 'step3.json'
mov_info = 'step3_mov_info.json'

with open(labels_json, 'r') as f:
    labels = json.load(f)
    
with open(mov_info, 'r') as f:
    mov_info = json.load(f)
    
# REMOVE LATER AS LABELS WILL BE GENERATED AUTOMATICALLY
id = 1
for label in labels:
    label['id'] = id
    id += 1

video_path = mov_info['video_path']
total_frames = mov_info['total_frames']
duration = mov_info['duration']
fps = mov_info['fps']

# Turn labels into a pandas DataFrame
df = pd.DataFrame(labels)
df = df.sort_values(by='timestamp')

# If the Frame number appears multiple times, use the one whose id is the largest
df = df.drop_duplicates(subset='frame', keep='last')
df = df.drop(columns=['id', 'timestamp'])

# Create a full range of frames
full_frame_range = pd.DataFrame({'frame': range(1, total_frames + 1)})

# Merge with the original dataframe to fill in missing frames
df_full = pd.merge(full_frame_range, df, on='frame', how='left')

# Forward fill the missing values using the previous frame's labels
df_full.fillna(method='ffill', inplace=True)

# Optionally, you might want to reset the index
df_full = df_full.reset_index(drop=True)

# If row a and row c have the same teeth, lips or action values, but row b has different values, then row b is incorrect and should be changed to the same as row a
for i, row in df_full.iterrows():
    if i == 0:
        continue

    prev_row = df_full.iloc[i - 1]
    curr_row = df_full.iloc[i]

    for col in ['teeth', 'lips', 'action']:
        if prev_row[col] == curr_row[col]:
            continue

        if prev_row[col] == df_full.iloc[i + 1][col]:
            df_full.at[i, col] = prev_row[col]
            
df_full['chew_count'] = None

chew_count = 0
for i, row in df_full.iterrows():
    if i == 0:
        continue
    
    if row['action'] == 'chew' and df_full.iloc[i - 1]['teeth'].lower() == 'closed' and row['teeth'].lower() == 'open':
        chew_count += 1
    df_full.at[i, 'chew_count'] = chew_count

# Save the final dataframe to a CSV file
df_full.to_csv('step4.csv', index=False)
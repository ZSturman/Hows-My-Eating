# Combine Step1 and Step6 csv

import pandas as pd

# Load the manually labeled data
manual_df = pd.read_csv('step6.csv')

# Load the OpenCV-generated features
features_df = pd.read_csv('step2.csv')

# Merge the datasets on 'frame'
merged_df = pd.merge(features_df, manual_df[['frame', 'teeth', 'lips', 'action']], on='frame')

# Save the combined data to a new CSV file
merged_df.to_csv('step7b.csv', index=False)

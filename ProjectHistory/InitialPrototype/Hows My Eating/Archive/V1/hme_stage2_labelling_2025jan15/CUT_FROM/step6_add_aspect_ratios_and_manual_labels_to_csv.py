# load in step 2.csv and step6.csv and merge them together using the frame column
#
import pandas as pd

# Load the manually labeled data
manual_df = pd.read_csv('step6.csv')

# Load the OpenCV-generated features
features_df = pd.read_csv('step2.csv')

# Merge the datasets on 'frame'
merged_df = pd.merge(features_df, manual_df, on='frame')

print(merged_df.head())
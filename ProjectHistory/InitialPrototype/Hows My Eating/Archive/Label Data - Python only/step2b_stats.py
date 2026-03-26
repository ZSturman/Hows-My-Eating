# step2b.py
# Description: This script reads the CSV file generated in step 2 and calculates statistical details for each column.
import pandas as pd
import numpy as np
import json
from scipy import stats

# Specify the input CSV file and output JSON file paths
csv_file_path = 'step2.csv'

df = pd.read_csv(csv_file_path)

# Initialize a dictionary to hold statistical details for each column
stats_dict = {}

# Function to detect outliers using z-score
def find_outliers_zscore(data):
    z_scores = stats.zscore(data)
    return data[np.abs(z_scores) > 3]

# Loop through each column and calculate statistical details
for column in df.columns[2:]:  # Skipping 'frame' and 'timestamp' columns
    column_data = df[column]
    
    stats_dict[column] = {
        'min': column_data.min(),
        'max': column_data.max(),
        'mean': column_data.mean(),
        'median': column_data.median(),
        'std_dev': column_data.std(),
        'variance': column_data.var(),
        'outliers': find_outliers_zscore(column_data).tolist(),
        'quartiles': {
            'Q1': column_data.quantile(0.25),
            'Q3': column_data.quantile(0.75),
            'IQR': column_data.quantile(0.75) - column_data.quantile(0.25)
        },
        'skewness': column_data.skew(),
        'kurtosis': column_data.kurtosis(),
    }

# Write the statistical details to a JSON file
json_file_path = 'step2b.json'  # Replace with your desired output file path
with open(json_file_path, 'w') as json_file:
    json.dump(stats_dict, json_file, indent=4)

print(f"Statistical summary has been successfully written to {json_file_path}")
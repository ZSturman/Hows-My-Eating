import os
import csv
import json
import pandas as pd
import numpy as np

# Function to compare thresh_ columns with manually labeled 'teeth' and 'lips' columns
def compare_csv(auto_csv_path, manual_df, half_way_point):
    auto_df = pd.read_csv(auto_csv_path)
    
    # Initialize a dictionary to hold the results
    result_dict = {}

    # Weighting factors for 'open' and 'closed' values
    open_weight = 2.0  # Give more importance to correct 'open' predictions
    closed_weight = 1.0  # Still consider 'closed' but with less weight

    # Iterate through each threshold column in the automated CSV
    for col in ['thresh_1', 'thresh_2', 'thresh_3', 'thresh_4', 'thresh_5']:
        # Initialize the inner dictionary for teeth and lips comparison
        result_dict[col] = {'teeth': 0, 'lips': 0}
        
        # Compare teeth values
        teeth_open_correct = ((auto_df[col].str.lower() == 'open') & (manual_df['teeth'].str.lower() == 'open')).sum()
        teeth_closed_correct = ((auto_df[col].str.lower() == 'closed') & (manual_df['teeth'].str.lower() == 'closed')).sum()
        
        # Calculate weighted score
        teeth_weighted_score = (teeth_open_correct * open_weight) + (teeth_closed_correct * closed_weight)
        result_dict[col]['teeth'] = int(teeth_weighted_score)
        
        if teeth_weighted_score < half_way_point * (open_weight + closed_weight) / 2:
            result_dict[col]['teeth_flip'] = True
        else:
            result_dict[col]['teeth_flip'] = False
           
        # Compare lips values
        lips_open_correct = ((auto_df[col].str.lower() == 'open') & (manual_df['lips'].str.lower() == 'open')).sum()
        lips_closed_correct = ((auto_df[col].str.lower() == 'closed') & (manual_df['lips'].str.lower() == 'closed')).sum()
        
        # Calculate weighted score
        lips_weighted_score = (lips_open_correct * open_weight) + (lips_closed_correct * closed_weight)
        result_dict[col]['lips'] = int(lips_weighted_score)
        
        if lips_weighted_score < half_way_point * (open_weight + closed_weight) / 2:
            result_dict[col]['lips_flip'] = True
        else:
            result_dict[col]['lips_flip'] = False
    
    return result_dict

# Load step6.csv
manual_labels_csv = 'step6.csv'
manual_labels = pd.read_csv(manual_labels_csv)

# List all files in step3_dir that end with .csv
step3_dir = "step3"
csv_files = [f for f in os.listdir(step3_dir) if f.endswith('.csv')]

mov_info = 'step5_mov_info.json'

with open(mov_info, 'r') as f:
    mov_info = json.load(f)
    
total_frames = mov_info['total_frames']
half_way_point = total_frames // 2

json_data = []

for csv_file in csv_files:
    result = compare_csv(f'{step3_dir}/{csv_file}', manual_labels, half_way_point)
    
    # Save the results to json dictionary
    json_data.append({
        'csv_file': csv_file,
        'results': result
    })
    
# Save the results to a JSON file
with open('step7.json', 'w') as f:
    json.dump(json_data, f, indent=2)

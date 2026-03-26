# step9.py
# Description: This script processes the data from step8 and selects the best thresholds for 'teeth' and 'lips' per feature.

import json

# Load the data from step8.json
with open('step8.json', 'r') as f:
    data = json.load(f)

# Initialize a dictionary to hold the best thresholds for each feature
best_thresholds = {}

for feature in data:
    csv_file = feature['csv']
    feature_name = csv_file.replace('_thresholds.csv', '')

    # For 'lips', get the best threshold (rank 1)
    lips_best = feature['lips']['1']
    lips_threshold = lips_best['thresh']
    lips_flipped = lips_best['flipped']
    lips_num_correct = lips_best['num_correct']

    # For 'teeth', get the best threshold (rank 1)
    teeth_best = feature['teeth']['1']
    teeth_threshold = teeth_best['thresh']
    teeth_flipped = teeth_best['flipped']
    teeth_num_correct = teeth_best['num_correct']

    # Store in the dictionary
    best_thresholds[feature_name] = {
        'lips': {
            'threshold': lips_threshold,
            'flipped': lips_flipped,
            'num_correct': lips_num_correct
        },
        'teeth': {
            'threshold': teeth_threshold,
            'flipped': teeth_flipped,
            'num_correct': teeth_num_correct
        }
    }

# Save the best thresholds to a JSON file
with open('step9.json', 'w') as f:
    json.dump(best_thresholds, f, indent=4)

print("Best thresholds per feature have been saved to 'step9.json'")

# step 8.py
# Description: This script processes the data from step 7 and ranks the results based on the number of correct frames.
import json

# Step 1: Load JSON files
step_7_json = 'step7.json'
mov_info = 'step5_mov_info.json'

with open(mov_info, 'r') as f:
    mov_info = json.load(f)

total_frames = mov_info['total_frames']

with open(step_7_json, 'r') as f:
    data = json.load(f)

ranking_data = []

# Step 2: Process data and build the ranking structure
for item in data:
    csv_file = item['csv_file']
    results = item['results']
    
    csv_struct = {
        'csv': csv_file,
        'lips': {},
        'teeth': {}
    }
    
    for threshold, values in results.items():
        teeth_flip = values['teeth_flip']
        lips_flip = values['lips_flip']

        # Flip values if necessary
        if teeth_flip:
            values['teeth'] = total_frames - values['teeth']
        if lips_flip:
            values['lips'] = total_frames - values['lips']

        # Add teeth and lips data
        teeth_struct = {
            'thresh': threshold,
            'flipped': teeth_flip,
            'num_correct': values['teeth']
        }

        lips_struct = {
            'thresh': threshold,
            'flipped': lips_flip,
            'num_correct': values['lips']
        }

        csv_struct['teeth'][threshold] = teeth_struct
        csv_struct['lips'][threshold] = lips_struct

    ranking_data.append(csv_struct)

# Step 3: Flatten and rank the data
for csv_struct in ranking_data:
    lips_items = list(csv_struct['lips'].items())
    teeth_items = list(csv_struct['teeth'].items())

    # Sort by num_correct
    lips_sorted = sorted(lips_items, key=lambda x: x[1]['num_correct'], reverse=True)
    teeth_sorted = sorted(teeth_items, key=lambda x: x[1]['num_correct'], reverse=True)

    # Assign ranking
    csv_struct['lips'] = {rank: data for rank, (thresh, data) in enumerate(lips_sorted, start=1)}
    csv_struct['teeth'] = {rank: data for rank, (thresh, data) in enumerate(teeth_sorted, start=1)}

# Step 4: Save the output to a JSON file
with open('step8.json', 'w') as f:
    json.dump(ranking_data, f, indent=4)


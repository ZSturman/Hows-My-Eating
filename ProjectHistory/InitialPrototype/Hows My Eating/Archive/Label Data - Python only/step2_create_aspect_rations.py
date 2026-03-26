# step2.py
# Description: This script calculates the aspect ratios and distances between facial landmarks.
import pandas as pd
import csv

# Load the data
step1 = "step1.csv"
df = pd.read_csv(step1)

# Column names
mouth_width = "p49_p55"
top_lip_height = "p52_p63"
bottom_lip_height = "p67_p58"
between_lips = "p63_p67"
nose_to_lips = "p34_p52"
lips_to_chin = "p58_p9"

# Left side
left_anchor_to_top_lip_top_left = "p49_p51"
left_anchor_to_bottom_lip_bottom_left = "p49_p59"
left_anchor_to_top_lip_bottom_left = "p49_p62"
left_anchor_to_bottom_lip_top_left = "p49_p68"
left_anchor_to_top_lip_top_center = "p49_p52"
left_anchor_to_top_lip_bottom_center = "p49_p63"
left_anchor_to_bottom_lip_top_center = "p49_p67"
left_anchor_to_bottom_lip_bottom_center = "p49_p58"
left_anchor_to_chin = "p49_p9"
left_anchor_to_nose = "p49_p34"

# Right side
right_anchor_to_top_lip_top_right = "p55_p53"
right_anchor_to_bottom_lip_bottom_right = "p55_p57"
right_anchor_to_top_lip_bottom_right = "p55_p64"
right_anchor_to_bottom_lip_top_right = "p55_p66"
right_anchor_to_top_lip_top_center = "p55_p52"
right_anchor_to_top_lip_bottom_center = "p55_p63"
right_anchor_to_bottom_lip_top_center = "p55_p67"
right_anchor_to_bottom_lip_bottom_center = "p55_p58"
right_anchor_to_chin = "p55_p9"
right_anchor_to_nose = "p55_p34"

# Create a new CSV file and write the header
output_file = "step2.csv"
cols = ['frame', 'timestamp', 'aspect_ratio_nose_to_lips_lips_to_chin', 'aspect_ratio_between_lips_to_mouth_width', 'aspect_ratio_top_lip_heigh_to_mouth_width', 'aspect_ratio_bottom_lip_heigh_to_mouth_width',  'aspect_ratio__mouth_width__nose_to_chin', 'aspect_ratio__mouth_width__outside_lips', 
        'aspect_ratio__mouth_width__inside_lips', 'anchor_to_top_lip_top', 'anchor_to_bottom_lip_bottom', 
        'anchor_to_top_lip_bottom', 'anchor_to_bottom_lip_top', 'anchor_to_top_lip_top_center', 
        'anchor_to_top_lip_bottom_center', 'anchor_to_bottom_lip_top_center', 'anchor_to_bottom_lip_bottom_center', 
        'anchor_to_chin', 'anchor_to_nose']

with open(output_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=cols)
    writer.writeheader()

    for idx, row in df.iterrows():
        new_row = {}
        new_row['frame'] = row['frame']
        new_row['timestamp'] = row['timestamp']
        
        new_row['aspect_ratio_nose_to_lips_lips_to_chin'] = row[nose_to_lips] / row[lips_to_chin]
        new_row['aspect_ratio_between_lips_to_mouth_width'] = row[between_lips] / row[mouth_width]
        new_row['aspect_ratio_top_lip_heigh_to_mouth_width'] = row[top_lip_height] / row[mouth_width]
        new_row['aspect_ratio_bottom_lip_heigh_to_mouth_width'] = row[bottom_lip_height] / row[mouth_width]
        
        # Ratio Distance from nose to chin compared to width of the mouth current frame
        new_row['aspect_ratio__mouth_width__nose_to_chin'] = row[mouth_width] / (row[top_lip_height] + row[bottom_lip_height] + row[between_lips] + row[nose_to_lips] + row[lips_to_chin])
        
        # Aspect Ratio of mouth current frame
        new_row['aspect_ratio__mouth_width__outside_lips'] = row[mouth_width] / (row[top_lip_height] + row[bottom_lip_height] + row[between_lips] + row[nose_to_lips] + row[lips_to_chin])
        new_row['aspect_ratio__mouth_width__inside_lips'] = row[mouth_width] / row[between_lips]

        # Averaging out left and right side
        new_row['anchor_to_top_lip_top'] = (row[left_anchor_to_top_lip_top_left] + row[right_anchor_to_top_lip_top_right]) / 2
        new_row['anchor_to_bottom_lip_bottom'] = (row[left_anchor_to_bottom_lip_bottom_left] + row[right_anchor_to_bottom_lip_bottom_right]) / 2
        new_row['anchor_to_top_lip_bottom'] = (row[left_anchor_to_top_lip_bottom_left] + row[right_anchor_to_top_lip_bottom_right]) / 2
        new_row['anchor_to_bottom_lip_top'] = (row[left_anchor_to_bottom_lip_top_left] + row[right_anchor_to_bottom_lip_top_right]) / 2
        new_row['anchor_to_top_lip_top_center'] = (row[left_anchor_to_top_lip_top_center] + row[right_anchor_to_top_lip_top_center]) / 2
        new_row['anchor_to_top_lip_bottom_center'] = (row[left_anchor_to_top_lip_bottom_center] + row[right_anchor_to_top_lip_bottom_center]) / 2
        new_row['anchor_to_bottom_lip_top_center'] = (row[left_anchor_to_bottom_lip_top_center] + row[right_anchor_to_bottom_lip_top_center]) / 2
        new_row['anchor_to_bottom_lip_bottom_center'] = (row[left_anchor_to_bottom_lip_bottom_center] + row[right_anchor_to_bottom_lip_bottom_center]) / 2
        new_row['anchor_to_chin'] = (row[left_anchor_to_chin] + row[right_anchor_to_chin]) / 2
        new_row['anchor_to_nose'] = (row[left_anchor_to_nose] + row[right_anchor_to_nose]) / 2
        
        # Write the new_row to the CSV file
        writer.writerow(new_row)

print(f"Data written to {output_file}")
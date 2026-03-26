import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
import csv
import json
import sys
from typing import List, Dict, Optional
from matplotlib import colors 



class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

def calculate_triangle_area(pointA: Optional[Point], pointB: Optional[Point], pointC: Optional[Point]) -> float:
    """Calculates the area of the triangle formed by points A, B, and C."""
    if pointA and pointB and pointC:
        # Check for missing or invalid points
        if any(val < 0 or val != val for val in [pointA.x, pointA.y, pointB.x, pointB.y, pointC.x, pointC.y]):
            print(f"Invalid points detected: A({pointA.x}, {pointA.y}), B({pointB.x}, {pointB.y}), C({pointC.x}, {pointC.y})")
            return 0.0
        
        x1, y1 = pointA.x, pointA.y
        x2, y2 = pointB.x, pointB.y
        x3, y3 = pointC.x, pointC.y
        area = abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)
        
        if area == 0.0:
            print(f"Zero area calculated for points: A({x1}, {y1}), B({x2}, {y2}), C({x3}, {y3})")

        return area
    print("One or more points are None")
    return 0.0

def read_csv(file_path: str) -> List[Dict[str, str]]:
    """Reads CSV data and returns a list of rows as dictionaries."""
    data = []
    try:
        with open(file_path, mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return data

def validate_points(point_groups: List[List[str]], csv_data: List[Dict[str, str]]) -> List[List[str]]:
    """Validates that all points exist in the CSV data. Returns a filtered list of valid point groups."""
    valid_points = set()
    if csv_data:
        valid_points = {col.split('_')[1] for col in csv_data[0].keys() if 'Point' in col}
        print(f"Valid points extracted from CSV: {valid_points}")

    filtered_groups = []
    for group in point_groups:
        print(f"Checking point group: {group}")
        # Convert all points to strings before comparison
        if all(str(point) in valid_points for point in group):
            filtered_groups.append(group)
        else:
            print(f"Warning: One or more points in group {group} are invalid and will be skipped.")
    
    print(f"Filtered valid point groups: {filtered_groups}")
    return filtered_groups

def process_csv_data(csv_data: List[Dict[str, str]], point_groups: List[List[str]]) -> List[Dict]:
    """Processes CSV data, calculates the triangle areas, and returns the results."""
    results = []
    last_known_areas = [0.0] * len(point_groups)  # To store last known areas

    for row in csv_data:
        areas = []
        for idx, points in enumerate(point_groups):
            try:
                # Parse points from CSV and log values
                pointA = Point(float(row[f'Point_{points[0]}_x']), float(row[f'Point_{points[0]}_y']))
                pointB = Point(float(row[f'Point_{points[1]}_x']), float(row[f'Point_{points[1]}_y']))
                pointC = Point(float(row[f'Point_{points[2]}_x']), float(row[f'Point_{points[2]}_y']))

                area = calculate_triangle_area(pointA, pointB, pointC)
                if area > 0:
                    last_known_areas[idx] = area  # Update last known area
                areas.append(last_known_areas[idx])
            except (ValueError, KeyError) as e:
                print(f"Error processing row {row['Frame']}: {e}")
                # If there's an error, keep the last known areas
                areas = last_known_areas.copy()

        results.append({
            'Frame': row['Frame'],
            'Timestamp': row['Timestamp'],
            'Areas': areas
        })

    return results

def normalize_areas(areas: List[float]) -> List[float]:
    """Normalize the areas to be within the range [0, 1] and ensure they sum to at most 1."""
    total_area = sum(areas)
    if total_area > 0:
        normalized = [area / total_area for area in areas]
    else:
        normalized = areas
    
    return [max(0.0, min(area, 1.0)) for area in normalized]

def create_pie_chart_frames(data: List[Dict], colors: List[str], output_folder: str, fps=30):
    """Create frames of pie charts representing the triangle areas over time and show preview."""
    os.makedirs(output_folder, exist_ok=True)
    last_areas_visible = [True] * len(colors)  # Track visibility of each area

    for i, entry in enumerate(data):
        normalized_areas = normalize_areas(entry['Areas'])
        frame = entry['Frame']
        timestamp = entry['Timestamp']

        # Print the frame number to the console
        print(f"Generating frame: {frame}")

        # Determine which areas are calculated
        is_calculated = [area > 0 for area in entry['Areas']]  # Boolean list indicating if each area was calculated

        # Adjust colors and labels based on whether the area could be calculated
        adjusted_colors = []
        labels = []
        for idx, calculated in enumerate(is_calculated):
            if calculated:
                adjusted_colors.append(colors[idx])
                labels.append(f'{normalized_areas[idx] * 100:.3f}%')  # Display percentages to two decimal places
            else:
                labels.append('NA')

        # Calculate remaining area
        remaining_area = max(0.0, 1 - sum(normalized_areas))
        
        # Adjust for 'NA' display when needed
        if remaining_area > 0:
            normalized_areas.append(remaining_area)
            labels.append('NA')
            adjusted_colors.append('gray')

        plt.figure(figsize=(5, 5), dpi=100)
        plt.gca().set_facecolor((0, 0, 0, 0))  # Set the figure background to transparent

        if any(normalized_areas):
            wedges, texts = plt.pie(
                normalized_areas,
                labels=None,  # Set labels to None to remove labels outside of slices
                colors=adjusted_colors,
                startangle=140,
                autopct=None,  # Disable the percentage display outside the slices
                pctdistance=0.85
            )

            # Manually add percentages or "NA" to each wedge
            for idx, wedge in enumerate(wedges):
                angle = (wedge.theta2 + wedge.theta1) / 2
                x = 0.6 * np.cos(np.deg2rad(angle))
                y = 0.6 * np.sin(np.deg2rad(angle))
                
                plt.text(
                    x, y,
                    labels[idx],
                    ha='center', va='center', fontsize=12, weight='bold', color='black'
                )

            # Create a transparent center circle
            centre_circle = plt.Circle((0, 0), 0.70, fc=(0, 0, 0, 0))
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
        else:
            plt.pie([1], labels=None, colors=['gray'], startangle=140)

        plt.axis('equal')  # Ensure the pie chart is a circle
        plt.savefig(f'{output_folder}/frame_{i:03d}.png', transparent=True, bbox_inches='tight')

        # Display the frame
        img = cv2.imread(f'{output_folder}/frame_{i:03d}.png')
        cv2.imshow('Preview', img)
        cv2.waitKey(int(1000 / fps))

        plt.close()

    cv2.destroyAllWindows()

def main():
    # Check if there are enough arguments
    if len(sys.argv) < 10:
        print(json.dumps({"error": "Incorrect number of arguments. Usage: <csv_file_path> <triangle flags and hex colors> <output_filename>"}))
        return

    csv_file_path = sys.argv[1]
    output_filename = sys.argv[-1]  # The output filename is the last argument
    triangles = sys.argv[2:-1]  # Everything after the CSV and before the output filename

    # Parse the triangles and colors
    point_groups = []
    colors = []
    current_group = []

    for arg in triangles:
        if arg.startswith('-') and not arg.startswith('--'):
            current_group.append(arg[1:])  # Remove the leading '-' and add as a string
        elif arg.startswith('--'):
            colors.append(f'#{arg[2:]}')
            if current_group:
                point_groups.append(current_group)
                current_group = []

    # In case there is a last group without a trailing color
    if current_group:
        point_groups.append(current_group)

    print(f"Parsed point groups: {point_groups}")
    print(f"Parsed colors: {colors}")

    # Read and process CSV data
    csv_data = read_csv(csv_file_path)

    # Validate points against the CSV data
    point_groups = validate_points(point_groups, csv_data)

    if not point_groups:
        print("Error: No valid point groups found after validation.")
        return

    areas = process_csv_data(csv_data, point_groups)

    # Create output folder for frames
    output_folder = f'{output_filename}_frames'
    create_pie_chart_frames(areas, colors, output_folder)

    # Print the ffmpeg command with the correct output filename
    print(f"Now run the command: ffmpeg -framerate 30 -i {output_folder}/frame_%03d.png -c:v libvpx-vp9 -b:v 2M -pix_fmt yuva420p {output_filename}.webm")

if __name__ == '__main__':
    main()
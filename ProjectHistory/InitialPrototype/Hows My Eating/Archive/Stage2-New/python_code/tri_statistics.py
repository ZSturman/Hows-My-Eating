import csv
import sys
from typing import List, Dict, Optional


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


def calculate_triangle_area(pointA: Optional[Point], pointB: Optional[Point], pointC: Optional[Point]) -> float:
    """Calculates the area of the triangle formed by points A, B, and C."""
    if pointA and pointB and pointC:
        if any(val <= 0 for val in [pointA.x, pointA.y, pointB.x, pointB.y, pointC.x, pointC.y]):
            return 0.0  # Invalid points, return area as 0

        x1, y1 = pointA.x, pointA.y
        x2, y2 = pointB.x, pointB.y
        x3, y3 = pointC.x, pointC.y
        area = abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)
        return area
    return 0.0


def read_csv(file_path: str) -> List[Dict[str, str]]:
    """Reads CSV data and returns a list of rows as dictionaries."""
    try:
        with open(file_path, mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)


def process_csv_data(csv_data: List[Dict[str, str]], points: List[int]) -> Dict:
    """Processes CSV data and calculates statistics for triangle areas."""
    results = {
        'calculable_areas': 0,
        'non_calculable_areas': 0,
        'invalid_points': {p: {'invalid_x': 0, 'invalid_y': 0} for p in points}
    }

    for row in csv_data:
        try:
            # Extract points from CSV and create Point objects
            pointA = Point(float(row[f'Point_{points[0]}_x']), float(row[f'Point_{points[0]}_y']))
            pointB = Point(float(row[f'Point_{points[1]}_x']), float(row[f'Point_{points[1]}_y']))
            pointC = Point(float(row[f'Point_{points[2]}_x']), float(row[f'Point_{points[2]}_y']))

            # Check if points are valid
            for idx, point in enumerate([pointA, pointB, pointC]):
                point_name = points[idx]
                if point.x <= 0:
                    results['invalid_points'][point_name]['invalid_x'] += 1
                if point.y <= 0:
                    results['invalid_points'][point_name]['invalid_y'] += 1

            # Calculate triangle area
            area = calculate_triangle_area(pointA, pointB, pointC)
            if area > 0:
                results['calculable_areas'] += 1
            else:
                results['non_calculable_areas'] += 1

        except (ValueError, KeyError) as e:
            print(f"Error processing row: {e}")
            results['non_calculable_areas'] += 1

    return results


def main():
    # Get command line arguments
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <csv_file_path> <points>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    points = list(map(int, sys.argv[2:5]))

    # Read CSV data
    csv_data = read_csv(csv_file_path)

    # Process data and calculate results
    results = process_csv_data(csv_data, points)

    # Print results
    print("Results:")
    print(f"Number of rows with calculable triangle areas: {results['calculable_areas']}")
    print(f"Number of rows with non-calculable triangle areas: {results['non_calculable_areas']}")
    for point, counts in results['invalid_points'].items():
        print(f"Point {point}:")
        print(f"  Invalid x values: {counts['invalid_x']}")
        print(f"  Invalid y values: {counts['invalid_y']}")


if __name__ == '__main__':
    main()
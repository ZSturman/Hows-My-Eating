import csv
import json
import sys
from typing import List, Dict, Optional


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


def calculate_triangle_area(pointA: Optional[Point], pointB: Optional[Point], pointC: Optional[Point]) -> float:
    """Calculates the area of the triangle formed by points A, B, and C."""
    if pointA and pointB and pointC:
        # If any coordinate is NaN or -1, return 0 as the area.
        if any(val == -1 or val != val for val in [pointA.x, pointA.y, pointB.x, pointB.y, pointC.x, pointC.y]):
            return 0.0
        # Area calculation using the determinant formula
        x1, y1 = pointA.x, pointA.y
        x2, y2 = pointB.x, pointB.y
        x3, y3 = pointC.x, pointC.y
        area = abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)
        return area
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


def process_csv_data(csv_data: List[Dict[str, str]], point_names: List[str]) -> List[Dict]:
    """Processes CSV data, calculates the triangle areas, and returns the results."""
    results = []

    for row in csv_data:
        # Extract the points from the CSV row using the provided point names
        try:
            pointA = Point(float(row[point_names[0] + '_x']), float(row[point_names[0] + '_y']))
            pointB = Point(float(row[point_names[1] + '_x']), float(row[point_names[1] + '_y']))
            pointC = Point(float(row[point_names[2] + '_x']), float(row[point_names[2] + '_y']))
        except ValueError:
            # If there's a value error (e.g., NaN or -1), set the area to 0
            pointA, pointB, pointC = None, None, None

        area = calculate_triangle_area(pointA, pointB, pointC)

        results.append({
            'Frame': row['Frame'],
            'Timestamp': row['Timestamp'],
            'Area': area
        })

    return results


def main() -> str:
    if len(sys.argv) != 5:
        return json.dumps({"error": "Incorrect number of arguments. Usage: <csv_file_path> <point1> <point2> <point3>"})

    csv_file_path = sys.argv[1]
    point1 = sys.argv[2]
    point2 = sys.argv[3]
    point3 = sys.argv[4]

    # Read and process CSV data
    csv_data = read_csv(csv_file_path)
    areas = process_csv_data(csv_data, [point1, point2, point3])

    # Convert results to JSON format
    return json.dumps(areas, indent=4)


if __name__ == '__main__':
    result = main()
    print(result)
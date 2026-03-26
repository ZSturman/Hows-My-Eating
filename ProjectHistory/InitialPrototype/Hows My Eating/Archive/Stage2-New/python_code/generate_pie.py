import matplotlib.pyplot as plt
import numpy as np
import os
import csv
import itertools
from typing import List, Dict

def read_csv(file_path: str) -> List[Dict[str, str]]:
    """Reads CSV data and returns a list of rows as dictionaries."""
    data = []
    try:
        with open(file_path, mode="r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return data

def normalize_values(values: List[float]) -> List[float]:
    """Normalize the values to sum to 1."""
    total_value = sum(values)
    if total_value > 0:
        normalized = [value / total_value for value in values]
    else:
        normalized = [0.0 for _ in values]
    return normalized

def create_pie_chart_frames(
    data: List[Dict],
    value_keys: List[str],
    colors: Dict[str, str],
    output_folder: str,
):
    """Create frames of pie charts representing the values over time."""
    os.makedirs(output_folder, exist_ok=True)

    # Create a figure and axis outside the loop to reuse
    fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
    ax.set_facecolor((0, 0, 0, 0))  # Set the figure background to transparent

    for i, entry in enumerate(data):
        frame = entry.get("Frames", f"{i}")
        # Print the frame number to the console
        print(f"Generating pie chart for frame: {frame}")

        # Extract the values for the current frame
        values = []
        labels = []
        adjusted_colors = []
        for key in value_keys:
            try:
                value = float(entry.get(key, 0.0))
                values.append(value)
                labels.append(key)
                adjusted_colors.append(colors[key])
            except ValueError:
                values.append(0.0)
                labels.append(key)
                adjusted_colors.append(colors[key])

        # Normalize the values
        normalized_values = normalize_values(values)

        # Clear the axis for the new plot
        ax.clear()

        # Filter out zero values for the pie chart
        non_zero_indices = [idx for idx, val in enumerate(values) if val > 0]
        if not non_zero_indices:
            # If all values are zero, create an empty pie chart
            ax.pie([1], labels=None, colors=["gray"], startangle=140)
        else:
            filtered_values = [normalized_values[idx] for idx in non_zero_indices]
            filtered_labels = [labels[idx] for idx in non_zero_indices]
            filtered_colors = [adjusted_colors[idx] for idx in non_zero_indices]

            wedges, texts = ax.pie(
                filtered_values,
                labels=None,
                colors=filtered_colors,
                startangle=140,
                autopct=None,
                pctdistance=0.85,
            )

            # Manually add percentages to each wedge
            for idx, wedge in enumerate(wedges):
                angle = (wedge.theta2 + wedge.theta1) / 2
                x = 0.6 * np.cos(np.deg2rad(angle))
                y = 0.6 * np.sin(np.deg2rad(angle))

                ax.text(
                    x,
                    y,
                    f"{filtered_values[idx] * 100:.2f}%",
                    ha="center",
                    va="center",
                    fontsize=12,
                    weight="bold",
                    color="black",
                )

            # Create a transparent center circle
            centre_circle = plt.Circle((0, 0), 0.70, fc=(0, 0, 0, 0))
            ax.add_artist(centre_circle)

        ax.axis("equal")  # Ensure the pie chart is a circle

        # Display the plot without blocking
        plt.draw()
        plt.pause(0.001)  # Pause briefly to update the plot

        # Save the figure
        plt.savefig(
            f"{output_folder}/frame_{i:03d}.png",
            transparent=True,
            bbox_inches="tight",
        )

    # Close the figure after processing
    plt.close(fig)
    print(f"Frames saved in {output_folder}")

def main():
    # Define the path to the CSV file with precomputed areas and lengths
    csv_file_path = "data/areas_and_lengths.csv"  # Replace with the path to your new CSV file

    # Read the CSV data
    csv_data = read_csv(csv_file_path)

    if not csv_data:
        print("Error: No data read from CSV.")
        return

    # Define the keys (columns) for triangles and lines
    triangle_keys = ['T095258', 'T495558', 'T636709', 'T094955', 'T051358']
    line_keys = ['L4955', 'L5258', 'L0958', 'L0952']

    # Assign consistent colors to each triangle and line
    colors = {
        'T095258': "#FF9999",  # Light red
        'T495558': "#66B3FF",  # Light blue
        'T636709': "#99FF99",  # Light green
        'T094955': "#FFCC99",  # Light orange
        'T051358': "#C2C2F0",  # Light purple
        'L4955': "#FFB6C1",    # Light pink
        'L5258': "#87CEFA",    # Light sky blue
        'L0958': "#90EE90",    # Light green
        'L0952': "#FFDAB9",    # Peach puff
    }

    # Generate combinations of triangles (from 2 to 5)
    triangle_combinations = []
    for r in range(2, 6):  # From 2 to 5 triangles
        combinations = list(itertools.combinations(triangle_keys, r))
        triangle_combinations.extend(combinations)
    print(f"Total triangle combinations: {len(triangle_combinations)}")  # Should be 26

    # Generate pie charts for each triangle combination
    for idx, combo in enumerate(triangle_combinations):
        print(f"Processing triangle combination {idx + 1}/{len(triangle_combinations)}: {combo}")
        # Create output folder for this combination
        combo_name = '_'.join(combo)
        output_folder = f"Triangles_{combo_name}_frames"

        # Generate pie charts
        create_pie_chart_frames(csv_data, list(combo), colors, output_folder)

    # Generate combinations of lines (from 2 to 4)
    line_combinations = []
    for r in range(2, 5):  # From 2 to 4 lines
        combinations = list(itertools.combinations(line_keys, r))
        line_combinations.extend(combinations)
    print(f"Total line combinations: {len(line_combinations)}")  # Should be 11

    # Generate pie charts for each line combination
    for idx, combo in enumerate(line_combinations):
        print(f"Processing line combination {idx + 1}/{len(line_combinations)}: {combo}")
        # Create output folder for this combination
        combo_name = '_'.join(combo)
        output_folder = f"Lines_{combo_name}_frames"

        # Generate pie charts
        create_pie_chart_frames(csv_data, list(combo), colors, output_folder)

    print("All combinations processed.")

if __name__ == "__main__":
    main()
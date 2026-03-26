import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Load your data
file_path = 'output_data.csv'  # Replace with your actual file path
data = pd.read_csv(file_path)

# Extract relevant columns for the points
points = data[['Timestamp', 'Point 0 X', 'Point 0 Y', 'Point 1 X', 'Point 1 Y', 'Point 2 X', 'Point 2 Y']]

# Rename columns for convenience
points.columns = ['Timestamp', 'x1', 'y1', 'x2', 'y2', 'x3', 'y3']

# Extract x and y positions for the three points
x_coords = ['x1', 'x2', 'x3', 'x1']  # Closing the triangle by returning to the first point
y_coords = ['y1', 'y2', 'y3', 'y1']

# Initialize the plot
fig, ax = plt.subplots()
triangle, = ax.plot([], [], marker='o', linestyle='-', color='b')
ax.set_xlim(200, 300)  # Adjust these limits based on the dataset range for better visibility
ax.set_ylim(550, 700)  # Adjust these limits based on the dataset range for better visibility
ax.set_title('Triangle Size Over Time')
ax.set_xlabel('X Position')
ax.set_ylabel('Y Position')

# Update function for animation
def update(frame):
    x = [points.iloc[frame][coord] for coord in x_coords]
    y = [points.iloc[frame][coord] for coord in y_coords]
    triangle.set_data(x, y)
    ax.set_title(f"Frame: {frame} | Timestamp: {points.iloc[frame]['Timestamp']:.2f} seconds")
    return triangle,

# Create the animation
ani = FuncAnimation(fig, update, frames=len(points), blit=True, repeat=False)

plt.show()
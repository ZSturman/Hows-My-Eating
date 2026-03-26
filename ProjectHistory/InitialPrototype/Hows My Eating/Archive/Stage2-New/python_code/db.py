""" import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import numpy as np

# Function to calculate the distance between two points
def calculate_distance(point1, point2):
    return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

# Load the CSV file
csv_path = 'output_data.csv'
df = pd.read_csv(csv_path)

# Extract column names for lips, jawline, and hands points
lips_columns = [col for col in df.columns if 'Lips Point' in col]
jawline_columns = [col for col in df.columns if 'Jawline Point' in col]
hand_columns = [col for col in df.columns if 'Hand Point' in col]

# Calculate the number of points dynamically
lips_points_count = len(lips_columns) // 2  # Divide by 2 because each point has an X and Y
jawline_points_count = len(jawline_columns) // 2
hand_points_count = len(hand_columns) // 2

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the Dash app
app.layout = html.Div([
    # Dropdowns for selecting points
    dcc.Dropdown(
        id='select-points',
        options=[{'label': f'Jawline Point {i}', 'value': f'Jawline Point {i}'} for i in range(1, jawline_points_count + 1)] +
                [{'label': f'Lips Point {i}', 'value': f'Lips Point {i}'} for i in range(1, lips_points_count + 1)],
        multi=True,
        placeholder='Select 3 points'
    ),
    # Buttons to add/remove/clear points
    html.Button('Add 3 Points', id='add-points', n_clicks=0),
    html.Button('Remove Last 3 Points', id='remove-points', n_clicks=0),
    html.Button('Clear Points', id='clear-points', n_clicks=0),
    # Toggle for hand points
    dcc.Checklist(
        id='toggle-hands',
        options=[{'label': 'View Hand Points', 'value': 'show_hands'}],
        value=[]
    ),
    # Slider for number of frames
    dcc.Slider(
        id='frame-slider',
        min=3,
        max=250,
        step=1,
        value=50,
        marks={str(i): str(i) for i in range(3, 251, 25)},
    ),
    # Navigation buttons
    html.Button('Previous', id='prev-frame', n_clicks=0),
    html.Button('Next', id='next-frame', n_clicks=0),
    # Dropdown to adjust frame skip
    dcc.Dropdown(
        id='frame-skip',
        options=[{'label': f'{i} frames', 'value': i} for i in range(1, 11)],
        value=1,
        placeholder='Select frame skip'
    ),
    # Graph for triangles' areas
    dcc.Graph(id='triangle-area-graph'),
    # Graph for frame overlay comparison
    dcc.Graph(id='frame-overlay-graph'),
    # Minimaps
    dcc.Graph(id='minimap-graph'),
    # Video display
    html.Div([
        html.Video(id='original-video', controls=True, src='path/to/original_video.mp4'),
        html.Video(id='overlay-video', controls=True, src='path/to/overlay_video.mp4')
    ])
])

# Callback to handle point selection, adding, and clearing
@app.callback(
    Output('select-points', 'value'),
    [Input('add-points', 'n_clicks'),
     Input('remove-points', 'n_clicks'),
     Input('clear-points', 'n_clicks')],
    [State('select-points', 'value')]
)
def update_points(add_clicks, remove_clicks, clear_clicks, selected_points):
    ctx = dash.callback_context
    if not ctx.triggered:
        return selected_points
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'add-points':
        if selected_points and len(selected_points) < 6:
            return selected_points + selected_points[:3]
    elif trigger == 'remove-points':
        if selected_points and len(selected_points) >= 3:
            return selected_points[:-3]
    elif trigger == 'clear-points':
        return []
    return selected_points

# Callback to handle frame navigation
@app.callback(
    Output('frame-slider', 'value'),
    [Input('prev-frame', 'n_clicks'),
     Input('next-frame', 'n_clicks')],
    [State('frame-slider', 'value'),
     State('frame-skip', 'value')]
)
def navigate_frames(prev_clicks, next_clicks, current_frame, frame_skip):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_frame
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'prev-frame':
        return max(3, current_frame - frame_skip)
    elif trigger == 'next-frame':
        return min(250, current_frame + frame_skip)
    return current_frame

# Callback to update the triangle area graph
@app.callback(
    Output('triangle-area-graph', 'figure'),
    [Input('select-points', 'value'),
     Input('frame-slider', 'value')]
)
def update_triangle_area_graph(selected_points, frame_number):
    if len(selected_points) < 3:
        return go.Figure()
    # Extract points for the selected frame
    frame_data = df[df['Frame'] == frame_number]
    points = [(frame_data[f'{p} X'].values[0], frame_data[f'{p} Y'].values[0]) for p in selected_points]
    
    # Calculate the area of the triangles formed by selected points
    area = 0.5 * abs(points[0][0] * (points[1][1] - points[2][1]) + points[1][0] * (points[2][1] - points[0][1]) + points[2][0] * (points[0][1] - points[1][1]))
    
    # Create the graph
    fig = go.Figure(data=[go.Scatter(x=[p[0] for p in points], y=[p[1] for p in points], mode='markers+lines', fill='toself')])
    fig.update_layout(title=f'Triangle Area: {area:.2f}')
    return fig

# Additional callbacks to handle overlay graph, minimap, and video sync
# (Implement further callbacks as needed)

if __name__ == '__main__':
    app.run_server(debug=True) """
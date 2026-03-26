# step3_label_data.py
# Description: This script allows you to label the open/close of teeth and lips, and the action (bite, chew, other) in a video.
import cv2
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, Scale, HORIZONTAL
import os

# # Function to choose a video file
# def choose_file():
#     video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
#     return video_path

# def get_mov_info(file_path):
#     try:
#         # Execute ffprobe command to get duration, fps, width, and height
#         result = subprocess.run(
#             [
#                 "ffprobe",
#                 "-v", "error",
#                 "-select_streams", "v:0",
#                 "-show_entries", "stream=width,height,r_frame_rate",
#                 "-show_entries", "format=duration",
#                 "-of", "json",
#                 file_path
#             ],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True
#         )

#         # Check for errors
#         if result.returncode != 0:
#             print(f"Error: {result.stderr.strip()}")
#             return None

#         # Parse the JSON output from ffprobe
#         info = json.loads(result.stdout)

#         # Extract duration
#         duration = float(info['format']['duration'])

#         # Extract width and height
#         width = int(info['streams'][0]['width'])
#         height = int(info['streams'][0]['height'])

#         # Calculate FPS from r_frame_rate
#         fps_str = info['streams'][0]['r_frame_rate']
#         num, denom = map(int, fps_str.split('/'))
#         fps = num / denom if denom != 0 else 0

#         # Calculate the number of frames
#         total_frames = int(duration * fps)

#         return {
#             'video_path': file_path,
#             'duration': duration,
#             'width': width,
#             'height': height,
#             'fps': fps,
#             'total_frames': total_frames
#         }

#     except Exception as e:
#         print(f"Exception occurred: {e}")
#         return None




# # Function to save markers to JSON
# def save_markers_to_json():
#     base_filename = 'step3'
#     json_filename = f'{base_filename}.json'
#     counter = 1

#     # Check if file exists and append a number if it does
#     while os.path.exists(json_filename):
#         json_filename = f'{base_filename}_{counter}.json'
#         counter += 1

#     with open(json_filename, 'w') as f:
#         json.dump(markers, f, indent=4)
#     print(f"Markers saved to {json_filename}")
    
# def save_mov_info_to_json():
#     base_filename = 'mov_info'
#     json_filename = f'{base_filename}.json'
#     counter = 1

#     # Check if file exists and append a number if it does
#     while os.path.exists(json_filename):
#         json_filename = f'{base_filename}_{counter}.json'
#         counter += 1

#     with open(json_filename, 'w') as f:
#         json.dump(info, f, indent=4)
#     print(f"Video information saved to {json_filename}")
    
    
# Function to set a custom marker and update mouth_state
def set_marker(teeth=None, lips=None, action=None):
    global mouth_state
    global id
    
    id += 1
    
    # Update mouth_state with provided values, if any
    if teeth:
        mouth_state['teeth'] = teeth
    if lips:
        mouth_state['lips'] = lips
    if action:
        mouth_state['action'] = action

    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    timestamp = current_frame / fps
    markers.append({
        'id': id,
        'frame': current_frame,
        'timestamp': round(timestamp, 4),
        'teeth': mouth_state['teeth'],
        'lips': mouth_state['lips'],
        'action': mouth_state['action']
    })
    print(f"Teeth: {mouth_state['teeth']} | Lips: {mouth_state['lips']} | Action: {mouth_state['action']} | Frame {current_frame} |  Timestamp {round(timestamp, 3)}")
    update_markers_display()

# Function to quit the program
def quit_program():
    # save_markers_to_json()
    # save_mov_info_to_json()
    cap.release()
    cv2.destroyAllWindows()
    root.quit()

# Function to toggle play/pause
def toggle_play_pause():
    global playing
    playing = not playing
    btn_play_pause.config(text="Pause" if playing else "Play")
    if playing:
        update_frame()

# Function to update the video frame
def update_frame():
    if playing:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Video Marker', frame)
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            frame_slider.set(current_frame)
            root.after(int(1000/fps), update_frame)
        else:
            toggle_play_pause()

# Function to move to a specific frame
def move_to_frame(val):
    val = max(0, int(val))  # Ensure the frame number is not less than 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, val)
    ret, frame = cap.read()
    if ret:
        cv2.imshow('Video Marker', frame)
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
        frame_slider.set(current_frame)

def update_markers_display():
    markers_display.config(state=tk.NORMAL)
    markers_display.insert(tk.END, f"Frame {markers[-1]['frame']}: Teeth: {markers[-1]['teeth']} | Lips: {markers[-1]['lips']} | Action: {markers[-1]['action']} ({markers[-1]['timestamp']}s)\n")
    markers_display.see(tk.END)
    markers_display.config(state=tk.DISABLED)

# Initialize the mouth_state to persist values
mouth_state = {
    "teeth": "Closed",
    "lips": "Closed",
    "action": "Other"
}

id = 0

# Initialize the main tkinter window
root = tk.Tk()
root.title("Label Open/Close")

# Create a frame for the markers display at the top
markers_frame = tk.Frame(root)
markers_frame.pack(fill=tk.X)

# Text widget to display markers above the slider
markers_display = tk.Text(markers_frame, height=4, state=tk.DISABLED)
markers_display.pack(fill=tk.X)

# Create a frame for the slider
slider_frame = tk.Frame(root)
slider_frame.pack(fill=tk.X)

# Frame slider to navigate through the video
frame_slider = Scale(slider_frame, from_=0, to=0, orient=HORIZONTAL, length=600, command=move_to_frame)
frame_slider.pack(fill=tk.X)

# Create a frame for the buttons
button_frame = tk.Frame(root, padx=10, pady=10)
button_frame.pack(side=tk.RIGHT, fill=tk.Y)

# Create playback control button (Play/Pause)
btn_play_pause = tk.Button(button_frame, text="Play (Space)", command=toggle_play_pause, padx=10, pady=5)
btn_play_pause.grid(row=0, column=0, columnspan=2, pady=5)

btn_back_one_frame = tk.Button(button_frame, text="Back 1 Frame (Left)", command=lambda: move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 2), padx=10, pady=5)
btn_back_one_frame.grid(row=1, column=0, pady=5)

btn_forward_one_frame = tk.Button(button_frame, text="Forward 1 Frame (Right)", command=lambda: move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES))), padx=10, pady=5)
btn_forward_one_frame.grid(row=1, column=1, pady=5)

btn_back_one_second = tk.Button(button_frame, text="Back 1 Second (Down)", command=lambda: move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - int(fps)), padx=10, pady=5)
btn_back_one_second.grid(row=2, column=0, pady=5)

btn_forward_one_second = tk.Button(button_frame, text="Forward 1 Second (Up)", command=lambda: move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)) + int(fps)), padx=10, pady=5)
btn_forward_one_second.grid(row=2, column=1, pady=5)

# Buttons for "Teeth"
label_teeth = tk.Label(button_frame, text="Teeth", font=('Arial', 12))
label_teeth.grid(row=3, column=0, columnspan=2, pady=(10, 0))

btn_teeth_open = tk.Button(button_frame, text="Open (1)", command=lambda: set_marker(teeth="Open"), padx=10, pady=5)
btn_teeth_open.grid(row=4, column=0, pady=5)

btn_teeth_closed = tk.Button(button_frame, text="Closed (2)", command=lambda: set_marker(teeth="Closed"), padx=10, pady=5)
btn_teeth_closed.grid(row=4, column=1, pady=5)

# Buttons for "Lips"
label_lips = tk.Label(button_frame, text="Lips", font=('Arial', 12))
label_lips.grid(row=5, column=0, columnspan=2, pady=(10, 0))

btn_lips_open = tk.Button(button_frame, text="Open (3)", command=lambda: set_marker(lips="Open"), padx=10, pady=5)
btn_lips_open.grid(row=6, column=0, pady=5)

btn_lips_closed = tk.Button(button_frame, text="Closed (4)", command=lambda: set_marker(lips="Closed"), padx=10, pady=5)
btn_lips_closed.grid(row=6, column=1, pady=5)

# Buttons for "Action"
label_action = tk.Label(button_frame, text="Action", font=('Arial', 12))
label_action.grid(row=7, column=0, columnspan=2, pady=(10, 0))

btn_action_bite = tk.Button(button_frame, text="Bite (5)", command=lambda: set_marker(action="Bite"), padx=10, pady=5)
btn_action_bite.grid(row=8, column=0, pady=5)

btn_action_chew = tk.Button(button_frame, text="Chew (6)", command=lambda: set_marker(action="Chew"), padx=10, pady=5)
btn_action_chew.grid(row=8, column=1, pady=5)

btn_action_swallow = tk.Button(button_frame, text="Swallow (7)", command=lambda: set_marker(action="Swallow"), padx=10, pady=5)
btn_action_swallow.grid(row=9, column=0, columnspan=2, pady=5)

btn_action_other = tk.Button(button_frame, text="Other (8)", command=lambda: set_marker(action="Other"), padx=10, pady=5)
btn_action_other.grid(row=9, column=0, columnspan=2, pady=5)

# Button to save and quit
btn_save_quit = tk.Button(button_frame, text="Save & Quit", command=quit_program, padx=10, pady=5)
btn_save_quit.grid(row=10, column=0, columnspan=2, pady=(20, 5))

# Function to handle keypress events for setting markers and toggling play/pause
def handle_keypress(event):
    key = event.keysym
    if key == 'space':
        toggle_play_pause()
    elif key == 'Up':
        move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)) + int(fps))
    elif key == 'Right':
        move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)))
    elif key == 'Down':
        move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - int(fps))
    elif key == 'Left':
        move_to_frame(int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 2)
    elif key == '1':
        set_marker(teeth="Open")
    elif key == '2':
        set_marker(teeth="Closed")
    elif key == '3':
        set_marker(lips="Open")
    elif key == '4':
        set_marker(lips="Closed")
    elif key == '5':
        set_marker(action="Bite")
    elif key == '6':
        set_marker(action="Chew")
    elif key == '7':
        set_marker(action="Swallow")
    elif key == '8':
        set_marker(action="Other")

# Bind keypress events to the main window
root.bind('<KeyPress>', handle_keypress)

# Button to choose a video file
# video_path = choose_file()
#video_path = "new_video.mov"

# if not video_path:
#     print("No video file selected.")
#     root.quit()

# Get video information
#info = get_mov_info(video_path)
# if not info:
#     print("Failed to retrieve video information.")
#     root.quit()

# Initialize video capture
cap = cv2.VideoCapture(video_path)

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

# Set the frame slider to the total number of frames
frame_slider.config(to=total_frames)

# List to store markers
markers = []

# Start video playback (initial state is paused)
playing = False

# Start the tkinter main loop
root.mainloop()
import os
import tempfile
import json
import csv
import shutil
import logging
import uuid

import pytest
import numpy as np
import pandas as pd
import cv2

# Import functions from pipeline modules
from executables.pipeline.split_video_by_events import extract_events, create_mov_chunks
from executables.pipeline.not_chew import export_not_chews
from executables.pipeline.mov_info import collect_mov_info
from executables.pipeline.labels_to_csv import merge_labels
from executables.pipeline.export_handler import export_file_handler
from executables.pipeline.compare_visuals import calculate_ratios, compare_visuals

# Create a dummy logger
logger = logging.getLogger("test")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

@pytest.fixture
def temp_dir():
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)

def test_extract_events(temp_dir):
    # Create a dummy CSV for extracting events.
    csv_file = os.path.join(temp_dir, "dummy_labels.csv")
    df = pd.DataFrame([
        {"frame": 1, "mouth": "closed", "action": ""},
        {"frame": 2, "mouth": "open", "action": "Bite"},
        {"frame": 3, "mouth": "closed", "action": ""},
        {"frame": 4, "mouth": "closed", "action": ""},
        {"frame": 5, "mouth": "open", "action": "Chew"},
        {"frame": 6, "mouth": "closed", "action": ""}
    ])
    df.to_csv(csv_file, index=False)
    events = extract_events(csv_file, logger)
    assert isinstance(events, list)
    assert len(events) == 2

def test_export_not_chews(temp_dir):
    # Create dummy JSON file for not_chew.
    json_data = [
        {"timestamp": 1.0, "userAcceleration": {"x": 0, "y": 0, "z": 0}, "gravity": {"x": 0, "y": 0, "z": 0}},
        {"timestamp": 2.0, "userAcceleration": {"x": 1, "y": 1, "z": 1}, "gravity": {"x": 1, "y": 1, "z": 1}}
    ]
    input_dir = os.path.join(temp_dir, "input_json")
    os.makedirs(input_dir, exist_ok=True)
    json_filepath = os.path.join(input_dir, "dummy.json")
    with open(json_filepath, "w") as f:
        json.dump(json_data, f)
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    result = export_not_chews(input_dir, output_dir, logger)
    assert result["status"] == "success"

def test_collect_mov_info(temp_dir, monkeypatch):
    # Create a dummy video file (black video: 1 second at 10 fps).
    video_path = os.path.join(temp_dir, "dummy.mov")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(video_path, fourcc, 10, (640, 480))
    for _ in range(10):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        video_writer.write(frame)
    video_writer.release()
    
    # Monkeypatch get_mov_from_dir to return our dummy video_path.
    def dummy_get_mov_from_dir(dir_path):
        return video_path
    monkeypatch.setattr("executables.pipeline.mov_info.get_mov_from_dir", dummy_get_mov_from_dir)
    
    result = collect_mov_info(temp_dir, "mov_info_test", logger)
    assert isinstance(result, dict)
    assert "mov_info" in result

def test_merge_labels(temp_dir):
    # Create dummy labels JSON.
    labels = [
        {"frame": 1, "mouth": "Closed", "action": "Other", "id": 1, "timestamp": 0.1},
        {"frame": 2, "mouth": "Open", "action": "Bite", "id": 2, "timestamp": 0.2},
        {"frame": 3, "mouth": "Closed", "action": "Other", "id": 3, "timestamp": 0.3}
    ]
    labels_json = os.path.join(temp_dir, "labels.json")
    with open(labels_json, "w") as f:
        json.dump(labels, f)
        
    # Create dummy mov_info JSON.
    mov_info = {"total_frames": 3}
    mov_info_json = os.path.join(temp_dir, "mov_info.json")
    with open(mov_info_json, "w") as f:
        json.dump(mov_info, f)
    output_csv = merge_labels(temp_dir, labels_json, mov_info_json, "merged_test", logger)
    assert output_csv is not None
    assert os.path.exists(output_csv)
    
def test_export_file_handler(temp_dir):
    # Create dummy CSV files for ratios, merged data, points data and chunks records.
    ratios_csv = os.path.join(temp_dir, "ratios.csv")
    merged_csv = os.path.join(temp_dir, "merged.csv")
    points_csv = os.path.join(temp_dir, "points.csv")
    chunks_csv = os.path.join(temp_dir, "chunks.csv")
    
    # Dummy ratios CSV.
    df_ratios = pd.DataFrame({
        "frame": [1, 2, 3],
        "timestamp": [0.1, 0.2, 0.3],
        "p49_p55": [50, 50, 50],
        "p52_p63": [10, 10, 10],
        "p67_p58": [15, 15, 15],
        "p63_p67": [5, 5, 5],
        "p34_p52": [20, 20, 20],
        "p58_p9": [25, 25, 25]
    })
    df_ratios.to_csv(ratios_csv, index=False)
    # Dummy merged data CSV.
    df_merged = pd.DataFrame({
        "frame": [1, 2, 3],
        "timestamp": [0.1, 0.2, 0.3],
        "bite_count": [0, 1, 1],
        "chew_count": [0, 0, 1],
        "chews_per_bite": [0, 0, 1]
    })
    df_merged.to_csv(merged_csv, index=False)
    # Dummy points CSV.
    df_points = pd.DataFrame({
        "frame": [1, 2, 3],
        "p49_p55": [50, 50, 50],
        "p52_p63": [10, 10, 10],
        "p67_p58": [15, 15, 15],
        "p63_p67": [5, 5, 5],
        "p34_p52": [20, 20, 20],
        "p58_p9": [25, 25, 25]
    })
    df_points.to_csv(points_csv, index=False)
    # Dummy chunks records CSV.
    df_chunks = pd.DataFrame({
        "start_frame": [2],
        "end_frame": [3],
        "file_path": ["dummy_chunk.mp4"]
    })
    df_chunks.to_csv(chunks_csv, index=False)
    
    # Create dummy motion data JSON.
    motion_data = [{
        "timestamp": 0.1,
        "userAcceleration": {"x": 0, "y": 0, "z": 0},
        "gravity": {"x": 0, "y": 0, "z": 0},
        "transformedRotation": {"x": 0, "y": 0, "z": 0, "w": 1},
        "rotationRate": {"x": 0, "y": 0, "z": 0},
        "attitude": {"pitch": 0, "roll": 0, "yaw": 0}
    }]
    motion_json = os.path.join(temp_dir, "motion.json")
    with open(motion_json, "w") as f:
        json.dump(motion_data, f)
        
    mov_info = {"duration": 0.1, "total_frames": 3}
    mov_info_file = os.path.join(temp_dir, "mov_info.json")
    with open(mov_info_file, "w") as f:
        json.dump(mov_info, f)
        
    output_folder = os.path.join(temp_dir, "output_folder")
    os.makedirs(output_folder, exist_ok=True)
    result = export_file_handler(
        output_folder,
        motion_json,
        mov_info_file,
        ratios_csv,
        points_csv,
        merged_csv,
        temp_dir,     # chunks directory
        chunks_csv,
        logger
    )
    assert isinstance(result, list)

def test_compare_functions(temp_dir):
    # Create dummy input CSV for calculate_ratios.
    df = pd.DataFrame({
        "frame": [1, 2, 3],
        "timestamp": [0.1, 0.2, 0.3],
        "p49_p55": [50, 50, 50],
        "p52_p63": [10, 10, 10],
        "p67_p58": [15, 15, 15],
        "p63_p67": [5, 5, 5],
        "p34_p52": [20, 20, 20],
        "p58_p9": [25, 25, 25]
    })
    input_csv = os.path.join(temp_dir, "input_ratios.csv")
    output_csv = os.path.join(temp_dir, "output_ratios.csv")
    df.to_csv(input_csv, index=False)
    
    calc_result = calculate_ratios(input_csv, output_csv, logger)
    assert os.path.exists(output_csv)
    
    compare_result = compare_visuals(input_csv, "compare_test", logger)
    assert isinstance(compare_result, dict)
    assert "csv_file" in compare_result

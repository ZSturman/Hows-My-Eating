import sys
import pytest

# Import executable entry-points
from executables import not_chew, mov_info, merge, exporting, compare, chunks

# Dummy functions to override external dependencies
def dummy_export_not_chews(collected_data_path, output_dir, logger):
    return {"dummy": "not_chew_success"}

def dummy_collect_mov_info(collected_data_path, mov_info_file_name, logger):
    return {"dummy": "mov_info_success"}

def dummy_merge_labels(dir_path, labelled_json_filepath, mov_info_file_path, merged_csv_output_name, logger):
    return "dummy_merged.csv"

def dummy_export_file_handler(output_folder_dir, motion_data_file, mov_info_file, ratios_data_file,
                              points_data_file, merged_data_file, chunks_dir, chunks_records, logger):
    return [{"dummy": "export_success"}]

def dummy_calculate_ratios(input_csv, output_csv, logger):
    return output_csv

def dummy_compare_visuals(input_csv_file_path, compare_csv_file_name, logger):
    return {"dummy": "compare_success"}

def dummy_extract_events(labels, logger):
    return [{"dummy_event": 1}]

def dummy_create_mov_chunks(events, video_clip, output_dir, logger):
    return [{"dummy": "chunk_success"}]

# Test for not_chew executable
def test_not_chew(monkeypatch):
    monkeypatch.setattr(not_chew, "export_not_chews", dummy_export_not_chews)
    sys.argv = ["not_chew", "dummy_path", "dummy_output", "--log_file", "dummy.log"]
    with pytest.raises(SystemExit) as exit_info:
        not_chew.main()
    assert exit_info.value.code == 0

# Test for mov_info executable
def test_mov_info(monkeypatch):
    monkeypatch.setattr(mov_info, "collect_mov_info", dummy_collect_mov_info)
    sys.argv = ["mov_info", "dummy_path", "dummy_mov_info.json", "--log_file", "dummy.log"]
    with pytest.raises(SystemExit) as exit_info:
        mov_info.main()
    assert exit_info.value.code == 0

# Test for merge executable
def test_merge(monkeypatch):
    monkeypatch.setattr(merge, "merge_labels", dummy_merge_labels)
    sys.argv = ["merge", "dummy_dir", "dummy_labelled.json", "dummy_mov_info.json", "dummy_output", "--log_file", "dummy.log"]
    with pytest.raises(SystemExit) as exit_info:
        merge.main()
    assert exit_info.value.code == 0

# Test for exporting executable
def test_exporting(monkeypatch):
    monkeypatch.setattr(exporting, "export_file_handler", dummy_export_file_handler)
    sys.argv = [
        "exporting",
        "dummy_output_folder",
        "dummy_motion.json",
        "dummy_mov_info.json",
        "dummy_ratios.csv",
        "dummy_points.csv",
        "dummy_merged.csv",
        "dummy_chunks_dir",
        "dummy_chunks.csv",
        "--log_file", "dummy.log"
    ]
    with pytest.raises(SystemExit) as exit_info:
        exporting.main()
    assert exit_info.value.code == 0

# Test for compare executable
def test_compare(monkeypatch):
    monkeypatch.setattr(compare, "compare_visuals", dummy_compare_visuals)
    sys.argv = ["compare", "dummy_input.csv", "dummy_compare", "--log_file", "dummy.log"]
    with pytest.raises(SystemExit) as exit_info:
        compare.main()
    assert exit_info.value.code == 0

# Test for chunks executable
def test_chunks(monkeypatch):
    monkeypatch.setattr(chunks, "extract_events", dummy_extract_events)
    monkeypatch.setattr(chunks, "create_mov_chunks", dummy_create_mov_chunks)
    sys.argv = ["chunks", "dummy_video.mov", "dummy_labels.csv", "dummy_output_dir", "--log_file", "dummy.log"]
    with pytest.raises(SystemExit) as exit_info:
        chunks.main()
    assert exit_info.value.code == 0

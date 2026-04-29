import tempfile
import unittest
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.field_tests import import_field_test_bundles


class FieldTestImportTests(unittest.TestCase):
    def test_import_prefers_labeled_motion_as_whole_reviewed_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "FieldTest-reviewed"
            bundle.mkdir()
            (bundle / "session_metadata.json").write_text('{"session_id":"FieldTest-reviewed"}')
            pd.DataFrame({
                "timestamp": [10.0, 10.1, 10.2],
                "ax": [0.1, 0.2, 0.3],
                "ay": [0.0, 0.0, 0.0],
                "az": [0.0, 0.0, 0.0],
                "gx": [0.0, 0.0, 0.0],
                "gy": [0.0, 0.0, 0.0],
                "gz": [0.0, 0.0, 0.0],
                "label": ["false", "true", "true"],
            }).to_csv(bundle / "labeled_motion.csv", index=False)
            (bundle / "motion.csv").write_text("timestamp,ax,ay,az,gx,gy,gz\n")
            (bundle / "feedback.csv").write_text("timestamp,event_type,predicted_state,corrected_state,window_start,window_end,note\n")

            manifest = import_field_test_bundles(
                root,
                root / "accepted",
                root / "manifests",
            )

            self.assertEqual(manifest["imported_count"], 1)
            imported_csv = Path(manifest["imported_sessions"][0]["csv_path"])
            imported = pd.read_csv(imported_csv)
            self.assertEqual(len(imported), 3)
            self.assertEqual(imported["label"].tolist(), [False, True, True])
            self.assertEqual(manifest["imported_sessions"][0]["event_type"], "reviewed_session")

    def test_old_feedback_window_bundle_still_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "FieldTest-legacy"
            bundle.mkdir()
            (bundle / "session_metadata.json").write_text('{"session_id":"FieldTest-legacy"}')
            pd.DataFrame({
                "timestamp": [10.0, 10.1, 10.2, 11.0],
                "ax": [0.1, 0.2, 0.3, 0.4],
                "ay": [0.0, 0.0, 0.0, 0.0],
                "az": [0.0, 0.0, 0.0, 0.0],
                "gx": [0.0, 0.0, 0.0, 0.0],
                "gy": [0.0, 0.0, 0.0, 0.0],
                "gz": [0.0, 0.0, 0.0, 0.0],
            }).to_csv(bundle / "motion.csv", index=False)
            pd.DataFrame({
                "timestamp": ["2026-04-29T00:00:00Z"],
                "event_type": ["false_positive"],
                "predicted_state": ["chewing"],
                "corrected_state": ["idle"],
                "window_start": [10.0],
                "window_end": [10.2],
                "note": [""],
            }).to_csv(bundle / "feedback.csv", index=False)

            manifest = import_field_test_bundles(
                root,
                root / "accepted",
                root / "manifests",
            )

            self.assertEqual(manifest["imported_count"], 1)
            imported = pd.read_csv(manifest["imported_sessions"][0]["csv_path"])
            self.assertEqual(imported["label"].tolist(), [False, False, False])


if __name__ == "__main__":
    unittest.main()


"""
Detect landmarks -> mouth signal -> chew peaks -> CSV labels.

Inputs:
  --video path/to/video.mov
  [--out-dir out]
  [--fs 100]                  # resample rate (Hz) for mouth signal / peak-picking
  [--band 0.5 3.0]            # chew band-pass (Hz)
  [--min-dist 0.35]           # min time between chews (s)
  [--thr-k 1.0]               # MAD threshold multiplier (adaptive)
  [--t0-abs 0.0]              # OPTIONAL: add this many seconds to *video* times
                               #          so peaks also have absolute timestamps

Outputs (in out-dir/):
  mouth_signal.csv    columns:
      frame, t_rel, t_abs(optional), mar, mar_bp, valid
  peaks.csv           columns:
      t_rel, t_abs(optional), height, width, source="video"

Notes:
- t_rel is seconds since video start.
- If you pass --t0-abs (absolute start time of the recording on host clock),
  t_abs will be included and can align directly with your IMU CSV.
"""

import argparse, csv, math, sys, os
from pathlib import Path

import cv2
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

# ---- Face landmarks (MediaPipe) ----
try:
    import mediapipe as mp
except Exception as e:
    print("Please install mediapipe: pip install mediapipe", file=sys.stderr); raise

# landmark indices (MediaPipe Face Mesh)

# MediaPipe Face Mesh landmark indices
UPPER_INNER = 13
LOWER_INNER = 14
LEFT_MOUTH  = 61
RIGHT_MOUTH = 291
LEFT_EYE    = 33
RIGHT_EYE   = 263
NOSE_TIP    = 1
CHIN        = 152

def bandpass(x, fs, lo, hi, order=4):
    b, a = butter(order, [lo/(fs/2), hi/(fs/2)], btype='band')
    return filtfilt(b, a, x)

def robust_z(x):
    med = np.median(x)
    mad = 1.4826*np.median(np.abs(x - med))
    return (x - med) / (mad + 1e-6), med, mad

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Directory containing .mov and .csv files")
    ap.add_argument("--fs", type=float, default=100.0)
    ap.add_argument("--band", type=float, nargs=2, default=[0.5, 3.0])
    ap.add_argument("--min-dist", type=float, default=0.35)
    ap.add_argument("--thr-k", type=float, default=1.0)
    ap.add_argument("--t0-abs", type=float, default=None,
                    help="If set, absolute start time (seconds) to add to t_rel to produce t_abs")
    return ap.parse_args()

def main():

    args = parse_args()
    input_dir = Path(args.input_dir)
    mov_files = list(input_dir.glob("*.mov"))
    processed_any = False
    for mov_path in mov_files:
        base = mov_path.stem
        csv_path = input_dir / f"{base}.csv"
        if not csv_path.exists():
            print(f"Skipping {mov_path.name}: no matching CSV.")
            continue

        # Create output directory structure
        parent_dir = input_dir / base
        out_labels_dir = parent_dir / "out_labels"
        out_labels_dir.mkdir(parents=True, exist_ok=True)

        # Set output paths
        overlay_video_path = parent_dir / "landmarks_overlay.mp4"
        ms_path = out_labels_dir / "mouth_signal.csv"
        events_path = out_labels_dir / "events.csv"

        # --- Begin original processing logic, adapted for new paths ---
        cap = cv2.VideoCapture(str(mov_path))
        if not cap.isOpened():
            print(f"Could not open video: {mov_path}", file=sys.stderr); continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or -1

        mpfm = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=False)

        t_rel = []
        mar_list = []
        valid = []
        nose_lip_dist = []
        chin_lip_dist = []
        overlay_frames = []

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = None

        frame = 0
        while True:
            ok, img = cap.read()
            if not ok: break
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            res = mpfm.process(rgb)

            this_valid = False
            mar = np.nan
            overlay_img = img.copy()
            mar = np.nan
            this_valid = False
            nose_dist = np.nan
            chin_dist = np.nan
            overlay_img = img.copy()
            if res.multi_face_landmarks:
                lm = res.multi_face_landmarks[0].landmark
                h, w = img.shape[:2]
                def P(i): p = lm[i]; return np.array([p.x*w, p.y*h], dtype=np.float32)

                u = P(UPPER_INNER)
                d = P(LOWER_INNER)
                l = P(LEFT_MOUTH)
                r = P(RIGHT_MOUTH)
                nose = P(NOSE_TIP)
                chin = P(CHIN)

                mouth_h = np.linalg.norm(u - d)
                mouth_w = max(1.0, np.linalg.norm(l - r))
                mar = float(mouth_h / mouth_w)
                lips_mid = 0.5 * (u + d)
                nose_dist = np.linalg.norm(nose - lips_mid)
                chin_dist = np.linalg.norm(chin - lips_mid)
                this_valid = True

                for pt, color in zip([u, d, l, r, nose, chin], [(0,0,255),(0,255,0),(255,0,0),(0,255,255),(255,255,0),(128,0,255)]):
                    cv2.circle(overlay_img, tuple(np.round(pt).astype(int)), 4, color, -1)
                cv2.line(overlay_img, tuple(np.round(u).astype(int)), tuple(np.round(d).astype(int)), (0,255,0), 2)
                cv2.line(overlay_img, tuple(np.round(l).astype(int)), tuple(np.round(r).astype(int)), (255,0,0), 2)
                cv2.line(overlay_img, tuple(np.round(nose).astype(int)), tuple(np.round(lips_mid).astype(int)), (255,255,0), 1)
                cv2.line(overlay_img, tuple(np.round(chin).astype(int)), tuple(np.round(lips_mid).astype(int)), (128,0,255), 1)

            t_rel.append(frame / fps)
            mar_list.append(mar)
            valid.append(1 if this_valid else 0)
            nose_lip_dist.append(nose_dist)
            chin_lip_dist.append(chin_dist)
            if out_writer is None:
                h, w = overlay_img.shape[:2]
                out_writer = cv2.VideoWriter(str(overlay_video_path), fourcc, fps, (w, h))
            out_writer.write(overlay_img)
            frame += 1

        cap.release()
        if out_writer is not None:
            out_writer.release()
        t_rel = np.asarray(t_rel, dtype=np.float64)
        mar_arr = np.asarray(mar_list, dtype=np.float32)
        valid = np.asarray(valid, dtype=np.int32)
        nose_lip_dist = np.asarray(nose_lip_dist, dtype=np.float32)
        chin_lip_dist = np.asarray(chin_lip_dist, dtype=np.float32)

        isn = np.isnan(mar_arr)
        if np.any(isn):
            good = ~isn
            if good.sum() >= 2:
                mar_arr[isn] = np.interp(t_rel[isn], t_rel[good], mar_arr[good])
            else:
                print("Too few valid landmarks; cannot interpolate.", file=sys.stderr)

        # ...existing code for resampling, filtering, writing CSVs...
        # (from line 181 onward, but update ms_path, events_path to new locations)

        # Resample to a uniform grid (fs) for filtering / peak picking
        fs = args.fs
        t_grid = np.arange(t_rel[0], t_rel[-1] + 1e-9, 1.0/fs)
        mar_rs = np.interp(t_grid, t_rel, mar_arr)

        detr = mar_rs - np.median(mar_rs)
        bp = bandpass(detr, fs, args.band[0], args.band[1])
        z, z_med, z_mad = robust_z(bp)

        thr = np.median(z) + args.thr_k * 1.0
        min_samples = int(args.min_dist * fs)
        peaks, props = find_peaks(z, height=thr, distance=min_samples, prominence=0.05)
        valleys, vprops = find_peaks(-z, height=thr, distance=min_samples, prominence=0.05)

        t_peaks_rel = t_grid[peaks]
        if args.t0_abs is not None:
            t_peaks_abs = args.t0_abs + t_peaks_rel
        else:
            t_peaks_abs = None
        t_valleys_rel = t_grid[valleys]
        if args.t0_abs is not None:
            t_valleys_abs = args.t0_abs + t_valleys_rel
        else:
            t_valleys_abs = None

        # Write mouth_signal.csv
        delta_mar = np.insert(np.diff(mar_arr), 0, 0.0)
        delta_nose_lip = np.insert(np.diff(nose_lip_dist), 0, 0.0)
        delta_chin_lip = np.insert(np.diff(chin_lip_dist), 0, 0.0)
        with ms_path.open("w", newline="") as f:
            w = csv.writer(f)
            header = [
                "frame", "t_rel", "t_abs", "mar", "delta_mar", "mar_bp",
                "nose_lip_dist", "delta_nose_lip_dist", "chin_lip_dist", "delta_chin_lip_dist", "valid"
            ]
            w.writerow(header)
            mar_bp_at_frame = np.interp(t_rel, t_grid, bp)
            for i in range(len(t_rel)):
                if args.t0_abs is not None:
                    t_abs_val = f"{(args.t0_abs + t_rel[i]):.6f}"
                else:
                    t_abs_val = ""
                row = [
                    i,
                    f"{t_rel[i]:.6f}",
                    t_abs_val,
                    f"{mar_arr[i]:.6f}",
                    f"{delta_mar[i]:.6f}",
                    f"{mar_bp_at_frame[i]:.6f}",
                    f"{nose_lip_dist[i]:.6f}",
                    f"{delta_nose_lip[i]:.6f}",
                    f"{chin_lip_dist[i]:.6f}",
                    f"{delta_chin_lip[i]:.6f}",
                    int(valid[i])
                ]
                w.writerow(row)

        # Write events.csv
        events = []
        widths = props.get("widths", np.zeros_like(peaks))
        widths_sec = widths / fs if widths is not None else np.zeros_like(peaks, dtype=float)
        for i, t in enumerate(t_peaks_rel):
            event = {
                "t_rel": t,
                "t_abs": t_peaks_abs[i] if t_peaks_abs is not None else None,
                "event": "open",
                "height_z": float(props["peak_heights"][i]),
                "width_s": float(widths_sec[i]) if i < len(widths_sec) else 0.0,
                "source": "video"
            }
            events.append(event)
        vwidths = vprops.get("widths", np.zeros_like(valleys))
        vwidths_sec = vwidths / fs if vwidths is not None else np.zeros_like(valleys, dtype=float)
        for i, t in enumerate(t_valleys_rel):
            valley_height_z = -vprops["peak_heights"][i]
            event = {
                "t_rel": t,
                "t_abs": t_valleys_abs[i] if t_valleys_abs is not None else None,
                "event": "closed",
                "height_z": float(valley_height_z),
                "width_s": float(vwidths_sec[i]) if i < len(vwidths_sec) else 0.0,
                "source": "video"
            }
            events.append(event)
        events.sort(key=lambda e: e["t_rel"])
        with events_path.open("w", newline="") as f:
            w = csv.writer(f)
            header = ["t_rel"]
            if args.t0_abs is not None:
                header.append("t_abs")
            header += ["event", "height_z", "width_s", "source"]
            w.writerow(header)
            for e in events:
                row = [f"{e['t_rel']:.6f}"]
                if args.t0_abs is not None:
                    row.append(f"{e['t_abs']:.6f}")
                row += [e["event"], f"{e['height_z']:.3f}", f"{e['width_s']:.3f}", e["source"]]
                w.writerow(row)

        # --- End original processing logic ---

        # Move original .mov and .csv into the parent_dir
        import shutil
        try:
            shutil.move(str(mov_path), str(parent_dir / mov_path.name))
            shutil.move(str(csv_path), str(parent_dir / csv_path.name))
        except Exception as e:
            print(f"Warning: could not move files for {base}: {e}")

        # Print summary for this pair
        print(f"Processed: {mov_path.name} + {csv_path.name}")
        print(f"  Output dir: {parent_dir}")
        print(f"  Overlay video: {overlay_video_path}")
        print(f"  Labels: {ms_path}, {events_path}")
        processed_any = True

    if not processed_any:
        print(f"No .mov/.csv pairs found in {input_dir}", file=sys.stderr)



if __name__ == "__main__":
    main()

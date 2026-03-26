import cv2, numpy as np, pandas as pd, argparse, sys, os
import shutil
from pathlib import Path

def robust_z(x):
    med = np.median(x)
    mad = 1.4826*np.median(np.abs(x - med))
    return (x - med) / (mad + 1e-6)

def parse_args():
    ap = argparse.ArgumentParser(description="Batch review/fix chew peaks with mouth+IMU strips")
    ap.add_argument("--input-dir", required=True, help="Directory containing subdirectories for review")
    ap.add_argument("--out", default="peaks_corrected.csv")  # Ignored, for backward compatibility
    ap.add_argument("--win", type=float, default=6.0, help="strip window seconds")
    ap.add_argument("--imu-smooth", type=float, default=0.25, help="seconds for simple EMA smoothing")
    ap.add_argument("--offset", type=float, default=None,
                    help="Optional constant offset to add to IMU times so they align to video (seconds). "
                         "Use only if your IMU lacks t_abs while peaks/mouth have t_rel or vice versa.")
    return ap.parse_args()

def load_csvs(peaks_path, mouth_path):
    P = pd.read_csv(peaks_path)
    M = pd.read_csv(mouth_path)
    # Required cols
    if "t_rel" not in P.columns:
        raise ValueError("peaks.csv must have t_rel")
    if "t_rel" not in M.columns or "mar" not in M.columns:
        raise ValueError("mouth_signal.csv must have t_rel and mar")
    # Optional absolute times
    has_abs = "t_abs" in P.columns and "t_abs" in M.columns
    # Prepare peaks dataframe for editing
    peaks = pd.DataFrame({
        "t_rel": P["t_rel"].astype(float),
        "t_abs": P["t_abs"].astype(float) if "t_abs" in P.columns else np.nan,
        "confirmed": np.ones(len(P), dtype=np.int32)     # default confirm
    })
    # Preserve chew labels if present; do not zero out
    if "chew" in P.columns:
        peaks["chew"] = P["chew"].astype(int)
    # Drop dupes & sort
    peaks = peaks.drop_duplicates(subset=["t_rel"]).sort_values("t_rel").reset_index(drop=True)
    # Load all relevant columns from mouth_signal.csv
    mouth_cols = ["t_rel", "mar", "delta_mar", "mar_bp", "nose_lip_dist", "delta_nose_lip_dist", "chin_lip_dist", "delta_chin_lip_dist", "valid"]
    mouth = pd.DataFrame({col: M[col].astype(float) for col in mouth_cols if col in M.columns})
    if "t_abs" in M.columns: mouth["t_abs"] = M["t_abs"].astype(float)
    return peaks, mouth, has_abs


def time_to_frame(t_rel, fps):
    return int(np.clip(round(t_rel * fps), 0, 10**9))

def frame_to_time(idx, fps):
    return idx / fps

def nearest_peak_index(peaks, t, tol=0.25):
    if peaks.empty: return None
    i = int(np.argmin(np.abs(peaks["t_rel"].values - t)))
    if abs(peaks.loc[i, "t_rel"] - t) <= tol: return i
    return None

def get_chew_spans(peaks):
    """Return list of (start, end) t_rel for chew spans where chew==1. If no 'chew' column, return []."""
    spans = []
    if "chew" not in peaks.columns:
        return []
    chew_mask = (peaks["chew"] == 1)
    chew_times = peaks["t_rel"].values
    chew_mask = chew_mask.values if hasattr(chew_mask, 'values') else chew_mask
    # Find contiguous regions where chew==1
    in_span = False
    start = None
    for i, is_chew in enumerate(chew_mask):
        if is_chew and not in_span:
            start = chew_times[i]
            in_span = True
        elif not is_chew and in_span:
            end = chew_times[i-1]
            if start is not None:
                spans.append((start, end))
            in_span = False
            start = None
    if in_span and start is not None:
        spans.append((start, chew_times[len(chew_mask)-1]))
    return spans

def invalidate_chews_touching_time(peaks, t_boundary, tol=1e-6):
    """If t_boundary matches the start or end of any chew span, clear chew=0 for that span."""
    chew_spans = get_chew_spans(peaks)
    chew_spans = chew_spans or []
    for s, e in chew_spans:
        if abs(s - t_boundary) < tol or abs(e - t_boundary) < tol:
            mask = (peaks["t_rel"] >= s) & (peaks["t_rel"] <= e)
            peaks.loc[mask, 'chew'] = 0
            print(f"[INFO] Chew invalidated: {s:.3f} to {e:.3f} (boundary {t_boundary:.3f})")
    """Return list of (start, end) t_rel for chew spans where chew==1. If no 'chew' column, return []."""
    spans = []
    if "chew" not in peaks.columns:
        return []
    chew_mask = (peaks["chew"] == 1)
    chew_times = peaks["t_rel"].values
    chew_mask = chew_mask.values if hasattr(chew_mask, 'values') else chew_mask
    # Find contiguous regions where chew==1
    in_span = False
    start = None
    for i, is_chew in enumerate(chew_mask):
        if is_chew and not in_span:
            start = chew_times[i]
            in_span = True
        elif not is_chew and in_span:
            end = chew_times[i-1]
            if start is not None:
                spans.append((start, end))
            in_span = False
            start = None
    if in_span and start is not None:
        spans.append((start, chew_times[len(chew_mask)-1]))
    return spans

def draw_overlay(frame, t_rel, fps, peaks, marker_ms, font_scale):
    h, w = frame.shape[:2]
    # Status text
    txt = f"t={t_rel:7.3f}s   fps={fps:.2f}   peaks={len(peaks)}"
    cv2.putText(frame, txt, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255,255,255), 2, cv2.LINE_AA)

    # Controls/instructions overlay (top left, multi-line)
    instructions = [
        "Controls:",
        "  Space: Play/Pause",
        "  a/d: Step frame backward/forward",
        "  s/w: Next/Prev open/closed",
        "  f/g: Step 1s backward/forward",
        "  o: Toggle open/closed at current frame",
        "  c: Toggle chew ON/OFF (closed..closed)",
        "  x: Remove LAST open/closed",
    "  Backspace/Delete: Remove event at cursor (within tolerance)",
        "  i: Toggle instructions",
        "  Ctrl+Z: Undo, Ctrl+Shift+Z (or Ctrl+Y): Redo",
        "  q or Esc: Quit"
    ]
    global show_instructions
    if show_instructions:
        # Draw semi-transparent background
        n_lines = len(instructions)
        pad = 10
        line_h = 32
        box_h = n_lines * line_h + pad*2
        box_w = 540
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 55), (5+box_w, 55+box_h), (0,0,0), -1)
        alpha = 0.5
        cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
        # Draw text
        for i, line in enumerate(instructions):
            y = 55 + pad + line_h//2 + i*line_h
            cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.95, (255,255,255), 2, cv2.LINE_AA)
    # (removed stray unused string and duplicate loop)

    # Timeline bar at bottom
    bar_h = 8
    cv2.rectangle(frame, (0, h-bar_h-4), (w, h-4), (40,40,40), -1)
    # Draw events on timeline (closed: blue, open: green, chew: magenta span)
    win = 3.0
    rel_events = peaks["t_rel"].values
    event_types = peaks["event"].values if "event" in peaks.columns else np.array(["closed"]*len(peaks))
    mask = (rel_events >= t_rel - win) & (rel_events <= t_rel + win)
    xs = ((rel_events[mask] - (t_rel - win)) / (2*win))
    for x, ev in zip(xs, event_types[mask]):
        X = int(np.clip(x,0,1) * w)
        color = (255,0,0) if ev=="closed" else (0,255,0) if ev=="open" else (255,0,255)
        cv2.line(frame, (X, h-4-bar_h), (X, h-4), color, 2)
    # Draw chew spans (vertical magenta brackets only)
    chew_spans = get_chew_spans(peaks)
    chew_spans = chew_spans or []
    for start, end in chew_spans:
        x0 = int(np.clip((start - (t_rel - win)) / (2*win), 0, 1) * w)
        x1 = int(np.clip((end - (t_rel - win)) / (2*win), 0, 1) * w)
        # Draw only left and right vertical lines (brackets)
        cv2.line(frame, (x0, h-4-bar_h-4), (x0, h-4), (255,0,255), 2)
        cv2.line(frame, (x1, h-4-bar_h-4), (x1, h-4), (255,0,255), 2)

    # Center marker
    cv2.line(frame, (w//2, 0), (w//2, h), (0, 180, 255), 1)

    # Event indicator if an event is “near now”
    near = np.where(np.abs(rel_events - t_rel) <= (marker_ms/1000.0))[0]
    for idx in near:
        ev = event_types[idx]
        color = (255,0,0) if ev=="closed" else (0,255,0) if ev=="open" else (255,0,255)
        cv2.circle(frame, (24+14*idx, 56), 6, color, -1)







def draw_waveform(w, h, t_rel, peaks, mouth, win=6.0):
    """Draw waveform image strip of size (h,w,3)"""
    strip = np.zeros((h, w, 3), dtype=np.uint8)
    # window around t_rel
    t0, t1 = t_rel - win/2, t_rel + win/2
    seg = mouth[(mouth["t_rel"] >= t0) & (mouth["t_rel"] <= t1)]
    if len(seg)==0: return strip
    ts = seg["t_rel"].values
    ys = seg["mar"].values
    # normalize y to 0-1
    ys = (ys - np.min(ys)) / (np.ptp(ys)+1e-6)
    xs = ((ts - t0) / (t1-t0) * (w-1)).astype(int)
    ys_pix = (h-1 - ys*(h-1)).astype(int)
    pts = np.stack([xs, ys_pix], axis=1)
    for i in range(1,len(pts)):
        cv2.line(strip, tuple(pts[i-1]), tuple(pts[i]), (0,255,0), 1)
    # mark events in window
    pk = peaks[(peaks["t_rel"]>=t0)&(peaks["t_rel"]<=t1)]
    for tr, ev in zip(pk["t_rel"].values, pk["event"].values if "event" in pk.columns else ["closed"]*len(pk)):
        X = int((tr - t0)/(t1-t0)*(w-1))
        color = (255,0,0) if ev=="closed" else (0,255,0) if ev=="open" else (255,0,255)
        cv2.line(strip, (X,0), (X,h-1), color, 2)
    # chew spans (vertical magenta brackets only)
    chew_spans = get_chew_spans(pk)
    chew_spans = chew_spans or []
    for start, end in chew_spans:
        x0 = int((start-t0)/(t1-t0)*(w-1))
        x1 = int((end-t0)/(t1-t0)*(w-1))
        cv2.line(strip, (x0, 0), (x0, h-1), (255,0,255), 1)
        cv2.line(strip, (x1, 0), (x1, h-1), (255,0,255), 1)
    # center line (current t)
    Xc = int((t_rel - t0)/(t1-t0)*(w-1))
    cv2.line(strip, (Xc,0), (Xc,h-1), (0,0,255), 1)
    return strip





def load_events(events_path):
    E = pd.read_csv(events_path)
    cols = list(E.columns)
    if "t_rel" not in cols or "event" not in cols:
        raise ValueError("events.csv must have columns t_rel and event")
    df = pd.DataFrame({
        "t_rel": E["t_rel"].astype(float),
        "t_abs": E["t_abs"].astype(float) if "t_abs" in cols else np.nan,
        "event": E["event"].astype(str),
        "confirmed": np.ones(len(E), dtype=int)
    }).drop_duplicates("t_rel").sort_values("t_rel").reset_index(drop=True)
    has_abs = "t_abs" in cols
    return df, has_abs

def load_mouth(mouth_path):
    M = pd.read_csv(mouth_path)
    if not {"t_rel","mar"}.issubset(M.columns): raise ValueError("mouth_signal.csv needs t_rel, mar")
    mouth_cols = ["t_rel", "mar", "delta_mar", "mar_bp", "nose_lip_dist", "delta_nose_lip_dist", "chin_lip_dist", "delta_chin_lip_dist", "valid"]
    mouth = pd.DataFrame({col: M[col].astype(float) for col in mouth_cols if col in M.columns})
    if "t_abs" in M.columns: mouth["t_abs"] = M["t_abs"].astype(float)
    return mouth, ("t_abs" in M.columns)

def load_imu(imu_path):
    # Flexible loader: t_abs or timestamp or t_rel, plus ax..gz
    D = pd.read_csv(imu_path)
    cols = {c.lower(): c for c in D.columns}
    # find time col
    time_col = None
    for key in ["t_abs","timestamp","time","t","t_rel"]:
        if key in cols: time_col = cols[key]; break
    if time_col is None:
        raise ValueError("IMU CSV needs a time column (t_abs/timestamp/time/t or t_rel)")
    # axes
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    ax = pick("ax","accx","accelx","acc_x")
    ay = pick("ay","accy","accely","acc_y")
    az = pick("az","accz","accelz","acc_z")
    gx = pick("gx","gyrox","gyrx","gyr_x")
    gy = pick("gy","gyroy","gyry","gyr_y")
    gz = pick("gz","gyroz","gyrz","gyr_z")
    for c in [ax,ay,az,gx,gy,gz]:
        if c is None: raise ValueError("IMU CSV needs ax,ay,az,gx,gy,gz columns (common aliases ok)")

    T = D[time_col].astype(float).to_numpy()
    # Return raw IMU columns for plotting
    imu = pd.DataFrame({
        "t": T,
        "ax": D[ax].astype(float).to_numpy(),
        "ay": D[ay].astype(float).to_numpy(),
        "az": D[az].astype(float).to_numpy(),
        "gx": D[gx].astype(float).to_numpy(),
        "gy": D[gy].astype(float).to_numpy(),
        "gz": D[gz].astype(float).to_numpy(),
    })
    return imu, (time_col.lower()=="t_abs")



def draw_strip(width, height, t_rel, series_t, series_y, peaks_t=None, chew_spans=None, color=(0,255,0), win=6.0, dash=False):
    """Render 1D series around t_rel into an (h,w,3) strip."""
    strip = np.zeros((height, width, 3), dtype=np.uint8)
    t0, t1 = t_rel - win/2, t_rel + win/2
    if len(series_t)==0: return strip
    mask = (series_t >= t0) & (series_t <= t1)
    if not np.any(mask): return strip
    ts = series_t[mask]; ys = series_y[mask]
    # scale 0..1
    ys = (ys - np.min(ys)) / (np.ptp(ys) + 1e-6)
    xs = ((ts - t0) / (t1 - t0) * (width-1)).astype(int)
    ys_pix = (height-1 - ys*(height-1)).astype(int)
    # draw
    for i in range(1, len(xs)):
        if dash and (i % 4 < 2): continue
        cv2.line(strip, (xs[i-1], ys_pix[i-1]), (xs[i], ys_pix[i]), color, 1)
    # peaks/events overlay (expects a list of dicts with t_rel and event)
    if peaks_t is not None and len(peaks_t):
        for tr, ev in peaks_t:
            if tr < t0 or tr > t1:
                continue
            X = int((tr - t0)/(t1 - t0)*(width-1))
            color_ev = (255,0,0) if ev=="closed" else (0,255,0) if ev=="open" else (255,0,255)
            cv2.line(strip, (X, 0), (X, height-1), color_ev, 2)
    # chew spans overlay (expects a list of (start, end) tuples)
    chew_spans = chew_spans or []
    for start, end in chew_spans:
        if end < t0 or start > t1:
            continue
        x0 = int((max(start, t0)-t0)/(t1-t0)*(width-1))
        x1 = int((min(end, t1)-t0)/(t1-t0)*(width-1))
        cv2.line(strip, (x0, 0), (x0, height-1), (255,0,255), 2)
        cv2.line(strip, (x1, 0), (x1, height-1), (255,0,255), 2)
    # center
    Xc = int((t_rel - t0)/(t1 - t0)*(width-1))
    cv2.line(strip, (Xc, 0), (Xc, height-1), (0,0,255), 1)
    return strip

# ---------- main ----------
def main():
    global show_instructions
    show_instructions = True
    args = parse_args()
    input_dir = Path(args.input_dir)
    subdirs = [d for d in input_dir.iterdir() if d.is_dir()]
    summary = []
    for subdir in subdirs:
        sub_summary = {"subdir": str(subdir), "source": None, "finalized": False}
        overlay_video = subdir / "landmarks_overlay.mp4"
        out_labels = subdir / "out_labels"
        chew_labels_path = out_labels / "chew_labels.csv"
        events_path = out_labels / "events.csv"
        mouth_path = out_labels / "mouth_signal.csv"
        if not overlay_video.exists():
            print(f"[WARN] Skipping {subdir}: missing landmarks_overlay.mp4")
            continue
        if not mouth_path.exists():
            print(f"[WARN] Skipping {subdir}: missing out_labels/mouth_signal.csv")
            continue
        # Prefer chew_labels.csv if present, else events.csv
        if chew_labels_path.exists():
            peaks, peaks_has_abs = load_events(str(chew_labels_path))
            sub_summary["source"] = "chew_labels.csv"
        elif events_path.exists():
            peaks, peaks_has_abs = load_events(str(events_path))
            sub_summary["source"] = "events.csv"
        else:
            print(f"[WARN] Skipping {subdir}: missing chew_labels.csv and events.csv")
            continue
        mouth, mouth_has_abs = load_mouth(str(mouth_path))
        # Remove any automatic chew labels at load
        if "chew" in peaks.columns:
            peaks["chew"] = 0
        # IMU
        imu_files = list(subdir.glob("imu-*.csv"))
        if not imu_files:
            imu_files = list(subdir.glob("video-*.csv"))
        imu_path = imu_files[0] if imu_files else None
        if imu_path:
            try:
                imu, imu_has_abs = load_imu(str(imu_path))
            except Exception as e:
                print(f"[WARN] IMU load failed in {subdir}: {e}")
                imu = None
                imu_has_abs = False
        else:
            print(f"[INFO] No IMU found in {subdir}; running without IMU strips.")
            imu = None
            imu_has_abs = False
        # Offset logic
        offset = args.offset
        if offset is None and imu_path:
            import csv
            with open(imu_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                first_row = next(reader, None)
                if first_row is not None:
                    try:
                        offset = -float(first_row[0])
                        print(f"[INFO] Set offset from first IMU timestamp: {offset}")
                    except Exception as e:
                        print(f"[WARN] Could not parse first IMU timestamp: {e}")
                else:
                    print(f"[WARN] IMU CSV {imu_path} is empty.")
            if offset is not None:
                try:
                    offset = float(offset)
                except Exception as e:
                    print(f"[WARN] Could not cast offset to float: {e}")
                    offset = 0.0
        # IMU t_rel
        if imu is not None:
            if imu_has_abs:
                if offset is not None:
                    imu_t_rel = imu["t"].to_numpy(dtype=float) + float(offset)
                elif mouth_has_abs:
                    t0 = float(mouth["t_abs"].iloc[0])
                    imu_t_rel = imu["t"].to_numpy() - t0
                elif peaks_has_abs:
                    t0 = float(peaks["t_abs"].iloc[0])
                    imu_t_rel = imu["t"].to_numpy() - t0
                else:
                    imu_t_rel = imu["t"].values - imu["t"].values[0]
            else:
                imu_t_rel = imu["t"].to_numpy(dtype=float) + float(offset if offset is not None else 0.0)
            imu_columns = [col for col in imu.columns if col not in ("t", "timestamp")]
            imu_wave_data = {col: imu[col].values for col in imu_columns}
            imu_time_axis = imu_t_rel
        else:
            imu_columns = []
            imu_wave_data = {}
            imu_time_axis = None
        # Video
        cap = cv2.VideoCapture(str(overlay_video))
        if not cap.isOpened():
            print(f"[WARN] Could not open video: {overlay_video}")
            continue
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or -1
        # Undo/redo
        undo_stack = []
        redo_stack = []
        import signal
        chew_state = None
        save_on_exit = True
        finalized = False
        # Save function (always to chew_labels.csv)
        def save_csv():
            if 'chew' not in peaks.columns:
                peaks['chew'] = 0
            cols = ["t_rel"]
            if "t_abs" in peaks.columns and not peaks["t_abs"].isna().all():
                cols.append("t_abs")
            cols += ["event", "confirmed", "chew"]
            out_peaks = peaks.copy()
            if 'event' in out_peaks.columns:
                out_peaks['event'] = out_peaks['event'].fillna('closed')
                out_peaks.loc[out_peaks['event'] == '', 'event'] = 'closed'
            out_peaks.sort_values("t_rel")[cols].to_csv(str(chew_labels_path), index=False, float_format="%.6f")
            print(f"[INFO] Saved {chew_labels_path} with {len(peaks)} events.")
        def handle_exit(*_):
            if save_on_exit:
                save_csv()
            cv2.destroyAllWindows()
            sys.exit(0)
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)
        # Finalize modal state
        show_finalize_modal = False
        finalize_confirmed = False
        finalize_message = ""
        # Main review loop
        try:
            tol = 0.25
            playing = False
            idx = 0
            changed = False
            while True:
                if playing:
                    idx = min(idx+1, n_frames-1 if n_frames>0 else idx+1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if not ok:
                    save_csv()
                    break
                t_rel = idx / fps
                h_wave = max(60, frame.shape[0] // (len(imu_columns) + 5))
                w_wave = max(320, frame.shape[1])
                waveforms = []
                event_overlay = list(zip(peaks["t_rel"].values, peaks["event"].values if "event" in peaks.columns else ["closed"]*len(peaks)))
                chew_spans = get_chew_spans(peaks)
                mar_strip = draw_strip(w_wave, h_wave, t_rel, mouth["t_rel"].values, mouth["mar"].values, peaks_t=event_overlay, chew_spans=chew_spans, color=(0,255,0), win=args.win)
                cv2.putText(mar_strip, "Mouth MAR (closed=blue, open=green, chew=magenta)", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,255,200), 2, cv2.LINE_AA)
                waveforms.append(mar_strip)
                if "delta_mar" in mouth.columns:
                    strip = draw_strip(w_wave, h_wave, t_rel, mouth["t_rel"].values, mouth["delta_mar"].values, peaks_t=event_overlay, chew_spans=chew_spans, color=(0,180,255), win=args.win)
                    cv2.putText(strip, "Delta MAR", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,180,255), 2, cv2.LINE_AA)
                    waveforms.append(strip)
                if "nose_lip_dist" in mouth.columns:
                    strip = draw_strip(w_wave, h_wave, t_rel, mouth["t_rel"].values, mouth["nose_lip_dist"].values, peaks_t=event_overlay, chew_spans=chew_spans, color=(255,200,0), win=args.win)
                    cv2.putText(strip, "Nose-Lip Dist", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,200,0), 2, cv2.LINE_AA)
                    waveforms.append(strip)
                if "delta_nose_lip_dist" in mouth.columns:
                    strip = draw_strip(w_wave, h_wave, t_rel, mouth["t_rel"].values, mouth["delta_nose_lip_dist"].values, peaks_t=event_overlay, chew_spans=chew_spans, color=(255,120,0), win=args.win)
                    cv2.putText(strip, "Delta Nose-Lip Dist", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,120,0), 2, cv2.LINE_AA)
                    waveforms.append(strip)
                if "chin_lip_dist" in mouth.columns:
                    strip = draw_strip(w_wave, h_wave, t_rel, mouth["t_rel"].values, mouth["chin_lip_dist"].values, peaks_t=event_overlay, chew_spans=chew_spans, color=(180,255,180), win=args.win)
                    cv2.putText(strip, "Chin-Lip Dist", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,255,180), 2, cv2.LINE_AA)
                    waveforms.append(strip)
                if "delta_chin_lip_dist" in mouth.columns:
                    strip = draw_strip(w_wave, h_wave, t_rel, mouth["t_rel"].values, mouth["delta_chin_lip_dist"].values, peaks_t=event_overlay, chew_spans=chew_spans, color=(0,255,180), win=args.win)
                    cv2.putText(strip, "Delta Chin-Lip Dist", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,180), 2, cv2.LINE_AA)
                    waveforms.append(strip)
                for col in imu_columns:
                    strip = draw_strip(
                        w_wave, h_wave, t_rel,
                        series_t=imu_time_axis,
                        series_y=imu_wave_data[col],
                        peaks_t=event_overlay,
                        chew_spans=chew_spans,
                        color=(255,255,255), win=args.win, dash=False
                    )
                    cv2.putText(strip, f"IMU {col}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220,220,255), 2, cv2.LINE_AA)
                    waveforms.append(strip)
                right_panel = np.vstack(waveforms)
                video_h = right_panel.shape[0]
                video_w = int(frame.shape[1] * (video_h / frame.shape[0]))
                video_resized = cv2.resize(frame, (video_w, video_h))
                draw_overlay(video_resized, t_rel, fps, peaks, marker_ms=250, font_scale=0.7)
                combo = np.hstack([video_resized, right_panel])
                # Finalize modal overlay
                if show_finalize_modal:
                    modal_h, modal_w = 320, 600
                    overlay = combo.copy()
                    y0 = combo.shape[0]//2 - modal_h//2
                    x0 = combo.shape[1]//2 - modal_w//2
                    cv2.rectangle(overlay, (x0, y0), (x0+modal_w, y0+modal_h), (0,0,0), -1)
                    alpha = 0.85
                    cv2.addWeighted(overlay, alpha, combo, 1-alpha, 0, combo)
                    lines = [
                        "Finalize labels?",
                        "Confirm finalization for this recording.",
                        "This will move media/IMU into a 'finalized' folder.",
                        "Continue? [Y/N]"
                    ]
                    for i, line in enumerate(lines):
                        y = y0 + 60 + i*60
                        cv2.putText(combo, line, (x0+40, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 3, cv2.LINE_AA)
                cv2.imshow("review", combo)
                key = cv2.waitKeyEx(1 if playing and not show_finalize_modal else 25)
                CTRL_MASK  = 0x200000
                SHIFT_MASK = 0x400000
                is_ctrl  = (key & CTRL_MASK) != 0
                is_shift = (key & SHIFT_MASK) != 0
                base = key & 0xFF
                if show_finalize_modal:
                    if base in (ord('y'), ord('Y')):
                        show_finalize_modal = False
                        finalize_confirmed = True
                    elif base in (ord('n'), ord('N')):
                        show_finalize_modal = False
                        finalize_confirmed = False
                        save_csv()
                        break
                    else:
                        continue
                if finalize_confirmed:
                    save_csv()
                    finalized_dir = subdir / "finalized"
                    finalized_dir.mkdir(exist_ok=True)
                    # Move files: landmarks_overlay.mp4, first imu-*.csv, first video-*.csv (if not same), .mov file matching subdir name
                    def move_with_rename(src, dst_dir):
                        dst = dst_dir / src.name
                        if dst.exists():
                            base, ext = os.path.splitext(src.name)
                            i = 1
                            while (dst_dir / f"{base}_{i}{ext}").exists():
                                i += 1
                            dst = dst_dir / f"{base}_{i}{ext}"
                        shutil.move(str(src), str(dst))
                        print(f"[INFO] Moved {src} -> {dst}")
                    # Move overlay video
                    if overlay_video.exists():
                        move_with_rename(overlay_video, finalized_dir)
                    # Move IMU
                    if imu_path and Path(imu_path).exists():
                        move_with_rename(Path(imu_path), finalized_dir)
                    # Move video-*.csv if not same as imu_path
                    video_csvs = list(subdir.glob("video-*.csv"))
                    for vcsv in video_csvs:
                        if not imu_path or Path(imu_path).resolve() != vcsv.resolve():
                            move_with_rename(vcsv, finalized_dir)
                            break
                    # Move .mov file matching subdir name
                    mov_file = subdir / (subdir.name + ".mov")
                    if mov_file.exists():
                        move_with_rename(mov_file, finalized_dir)
                    finalized = True
                    sub_summary["finalized"] = True
                    print(f"[INFO] Finalized {subdir}")
                    break
                # Navigation keys
                if key == ord('a'):
                    idx = max(0, idx - 1)
                elif key == ord('d'):
                    idx = min(n_frames - 1, idx + 1)
                elif key == ord('f'):
                    idx = max(0, idx - int(fps))
                elif key == ord('g'):
                    idx = min(n_frames - 1, idx + int(fps))
                if key in (ord('q'), 27):
                    show_finalize_modal = True
                elif key == ord(' '):
                    playing = not playing
                elif key == ord('n'):
                    t_rel_values = peaks["t_rel"].to_numpy()
                    nxt = t_rel_values[t_rel_values > t_rel]
                    if len(nxt):
                        idx = int(round(nxt[0] * fps))
                elif key == ord('p'):
                    undo_stack.append(peaks.copy(deep=True))
                    redo_stack.clear()
                    row = {"t_rel": t_rel, "t_abs": np.nan, "event": "closed", "confirmed": 1}
                    if "t_abs" in mouth.columns:
                        j = int(np.argmin(np.abs(mouth["t_rel"].to_numpy(dtype=float) - float(t_rel))))
                        t_abs_val = mouth.loc[j, "t_abs"]
                        try:
                            if isinstance(t_abs_val, np.generic):
                                v = t_abs_val.item()
                            else:
                                v = t_abs_val
                            if isinstance(v, complex):
                                v = v.real
                            if isinstance(v, (float, int, bool, np.number)):
                                row["t_abs"] = float(v)
                            else:
                                row["t_abs"] = float('nan')
                        except Exception:
                            row["t_abs"] = float('nan')
                    peaks = pd.concat([peaks, pd.DataFrame([row])], ignore_index=True)
                    peaks = peaks.drop_duplicates(["t_rel", "event"]).sort_values("t_rel").reset_index(drop=True)
                    changed = True
                elif key == ord('o'):
                    undo_stack.append(peaks.copy(deep=True))
                    redo_stack.clear()
                    tol = 1.0 / fps / 2.0
                    at_frame = peaks[(np.abs(peaks["t_rel"] - t_rel) < tol) & (peaks["event"].isin(["open", "closed"]))]
                    if not at_frame.empty:
                        event_idx = at_frame.index[0]
                        t_boundary = peaks.loc[event_idx, "t_rel"]
                        current_event = peaks.loc[event_idx, "event"]
                        new_event = "closed" if current_event == "open" else "open"
                        peaks.loc[event_idx, "event"] = new_event
                        invalidate_chews_touching_time(peaks, t_boundary, tol=tol)
                        changed = True
                    else:
                        prev_events = peaks[peaks["t_rel"] < t_rel]
                        if not prev_events.empty:
                            last_event = prev_events.iloc[-1]["event"]
                            new_event = "closed" if last_event == "open" else "open"
                        else:
                            new_event = "open"
                        row = {"t_rel": t_rel, "t_abs": np.nan, "event": new_event, "confirmed": 1}
                        if "t_abs" in mouth.columns:
                            j = int(np.argmin(np.abs(mouth["t_rel"].to_numpy(dtype=float) - float(t_rel))))
                            t_abs_val = mouth.loc[j, "t_abs"]
                            try:
                                if isinstance(t_abs_val, np.generic):
                                    v = t_abs_val.item()
                                else:
                                    v = t_abs_val
                                if isinstance(v, complex):
                                    v = v.real
                                if isinstance(v, (float, int, bool, np.number)):
                                    row["t_abs"] = float(v)
                                else:
                                    row["t_abs"] = float('nan')
                            except Exception:
                                row["t_abs"] = float('nan')
                        peaks = pd.concat([peaks, pd.DataFrame([row])], ignore_index=True)
                        peaks = peaks.drop_duplicates(["t_rel", "event"]).sort_values("t_rel").reset_index(drop=True)
                        changed = True
                elif key in (8, 127):
                    undo_stack.append(peaks.copy(deep=True)); redo_stack.clear()
                    tol = 1.0 / fps / 2.0
                    at_frame = peaks[(np.abs(peaks["t_rel"] - t_rel) < tol) & (peaks["event"].isin(["open","closed"]))]
                    if not at_frame.empty:
                        t_boundary = peaks.loc[at_frame.index[0], "t_rel"]
                        peaks = peaks.drop(at_frame.index[0]).reset_index(drop=True)
                        invalidate_chews_touching_time(peaks, t_boundary, tol=tol)
                        changed = True
                elif key == ord('x'):
                    chew_spans = get_chew_spans(peaks)
                    tol = 1.0 / fps / 2.0
                    removed = False
                    for s, e in chew_spans:
                        if abs(t_rel - s) < tol:
                            undo_stack.append(peaks.copy(deep=True)); redo_stack.clear()
                            mask = (peaks["t_rel"] >= s) & (peaks["t_rel"] <= e)
                            peaks.loc[peaks["t_rel"] == s, 'chew'] = 0
                            print(f"[INFO] Chew start removed at {s:.3f}")
                            removed = True
                            changed = True
                            break
                        elif abs(t_rel - e) < tol:
                            undo_stack.append(peaks.copy(deep=True)); redo_stack.clear()
                            mask = (peaks["t_rel"] >= s) & (peaks["t_rel"] <= e)
                            peaks.loc[peaks["t_rel"] == e, 'chew'] = 0
                            print(f"[INFO] Chew end removed at {e:.3f}")
                            removed = True
                            changed = True
                            break
                    if not removed:
                        print("[INFO] Not on a chew start or end frame; nothing removed.")
                elif base == ord('c'):
                    if chew_state is None:
                        undo_stack.append(peaks.copy(deep=True)); redo_stack.clear()
                        if 'chew' not in peaks.columns:
                            peaks['chew'] = 0
                        tol = 1.0 / fps / 2.0
                        at_frame = peaks[(np.abs(peaks["t_rel"] - t_rel) < tol) & (peaks["event"].isin(["open", "closed"]))]
                        if at_frame.empty:
                            row = {"t_rel": t_rel, "t_abs": np.nan, "event": "closed", "confirmed": 1}
                            if "t_abs" in mouth.columns:
                                j = int(np.argmin(np.abs(mouth["t_rel"].to_numpy(dtype=float) - float(t_rel))))
                                t_abs_val = mouth.loc[j, "t_abs"]
                                try:
                                    if isinstance(t_abs_val, np.generic):
                                        v = t_abs_val.item()
                                    else:
                                        v = t_abs_val
                                    if isinstance(v, complex):
                                        v = v.real
                                    if isinstance(v, (float, int, bool, np.number)):
                                        row["t_abs"] = float(v)
                                    else:
                                        row["t_abs"] = float('nan')
                                except Exception:
                                    row["t_abs"] = float('nan')
                            peaks = pd.concat([peaks, pd.DataFrame([row])], ignore_index=True)
                            peaks = peaks.drop_duplicates(["t_rel", "event"]).sort_values("t_rel").reset_index(drop=True)
                        chew_state = {"start_idx": idx, "start_t_rel": t_rel}
                        print(f"[INFO] Chew start marked at {t_rel:.3f}")
                        changed = True
                    else:
                        undo_stack.append(peaks.copy(deep=True)); redo_stack.clear()
                        if 'chew' not in peaks.columns:
                            peaks['chew'] = 0
                        tol = 1.0 / fps / 2.0
                        at_frame = peaks[(np.abs(peaks["t_rel"] - t_rel) < tol) & (peaks["event"].isin(["open", "closed"]))]
                        if at_frame.empty:
                            row = {"t_rel": t_rel, "t_abs": np.nan, "event": "closed", "confirmed": 1}
                            if "t_abs" in mouth.columns:
                                j = int(np.argmin(np.abs(mouth["t_rel"].to_numpy(dtype=float) - float(t_rel))))
                                t_abs_val = mouth.loc[j, "t_abs"]
                                try:
                                    if isinstance(t_abs_val, np.generic):
                                        v = t_abs_val.item()
                                    else:
                                        v = t_abs_val
                                    if isinstance(v, complex):
                                        v = v.real
                                    if isinstance(v, (float, int, bool, np.number)):
                                        row["t_abs"] = float(v)
                                    else:
                                        row["t_abs"] = float('nan')
                                except Exception:
                                    row["t_abs"] = float('nan')
                            peaks = pd.concat([peaks, pd.DataFrame([row])], ignore_index=True)
                            peaks = peaks.drop_duplicates(["t_rel", "event"]).sort_values("t_rel").reset_index(drop=True)
                        t_start = chew_state["start_t_rel"]
                        t_end = t_rel
                        if t_end < t_start:
                            t_start, t_end = t_end, t_start
                        mask = (peaks["t_rel"] >= t_start) & (peaks["t_rel"] <= t_end)
                        peaks.loc[mask, 'chew'] = 1
                        print(f"[INFO] Chew span set: {t_start:.3f} to {t_end:.3f}")
                        chew_state = None
                        changed = True
                elif is_shift and base == ord('C'):
                    chew_spans = get_chew_spans(peaks)
                    inside = None
                    for s, e in chew_spans:
                        if t_rel >= s and t_rel <= e:
                            inside = (s, e)
                            break
                    if inside is not None:
                        undo_stack.append(peaks.copy(deep=True)); redo_stack.clear()
                        if 'chew' not in peaks.columns:
                            peaks['chew'] = 0
                        s, e = inside
                        mask = (peaks["t_rel"] >= s) & (peaks["t_rel"] <= e)
                        peaks.loc[mask, 'chew'] = 0
                        print(f"[INFO] Chew span removed: {s:.3f} to {e:.3f}")
                        changed = True
                    chew_state = None
                elif key == ord('i'):
                    show_instructions = not show_instructions
                if (is_ctrl and not is_shift and (base == ord('z') or base == ord('Z'))) or key == 26:
                    if undo_stack:
                        redo_stack.append(peaks.copy(deep=True))
                        peaks = undo_stack.pop()
                        changed = True
                elif (is_ctrl and is_shift and (base == ord('z') or base == ord('Z'))) or (is_ctrl and (base == ord('y') or base == ord('Y'))) or key == 25:
                    if redo_stack:
                        undo_stack.append(peaks.copy(deep=True))
                        peaks = redo_stack.pop()
                        changed = True
            save_csv()
        finally:
            cv2.destroyAllWindows()
        print(f"[INFO] Subdir: {subdir}")
        print(f"[INFO] Source: {sub_summary['source']}")
        print(f"[INFO] Output: {chew_labels_path}")
        print(f"[INFO] Finalized: {'yes' if finalized else 'no'}")
        summary.append(sub_summary)
    # Print summary
    print("\nBatch review complete.")
    print(f"Processed {len(summary)} subdirectories.")
    for s in summary:
        print(f"- {s['subdir']}: source={s['source']}, finalized={'yes' if s['finalized'] else 'no'}")

if __name__ == "__main__":
    main()

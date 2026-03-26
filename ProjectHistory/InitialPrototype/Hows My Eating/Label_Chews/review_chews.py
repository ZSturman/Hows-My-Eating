#!/usr/bin/env python3
import cv2, numpy as np, pandas as pd, argparse, sys, signal
from pathlib import Path

def parse_args():
    ap = argparse.ArgumentParser(description="Chew-only reviewer (no events/confirmed)")
    ap.add_argument("--session-dir", required=True)
    ap.add_argument("--video", default=None, help="Override video path; else session_dir/video.mov")
    ap.add_argument("--win", type=float, default=6.0, help="waveform window seconds")
    ap.add_argument("--imu-smooth", type=float, default=0.25, help="EMA seconds for IMU display")
    ap.add_argument("--offset", type=float, default=None, help="Optional offset (s) added to IMU times")
    return ap.parse_args()

# --------- IMU loader (optional) ---------
def load_imu(imu_path: Path):
    if not imu_path.exists(): return None, False
    D = pd.read_csv(imu_path)
    cols = {c.lower(): c for c in D.columns}
    tcol = None
    for k in ["t_abs","timestamp","time","t","t_rel"]:
        if k in cols: tcol = cols[k]; break
    if tcol is None: return None, False
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    ax=pick("ax","accx","accelx","acc_x"); ay=pick("ay","accy","accely","acc_y"); az=pick("az","accz","accelz","acc_z")
    gx=pick("gx","gyrox","gyrx","gyr_x"); gy=pick("gy","gyroy","gyry","gyr_y"); gz=pick("gz","gyroz","gyrz","gyr_z")
    for c in [ax,ay,az,gx,gy,gz]:
        if c is None: return None, False
    T = D[tcol].astype(float).to_numpy()
    # Align IMU time to start at zero if using 'timestamp' column
    if tcol.lower() == "timestamp":
        T = T - T[0]
    acc = np.linalg.norm(D[[ax,ay,az]].astype(float).to_numpy(), axis=1)
    gyr = np.linalg.norm(D[[gx,gy,gz]].astype(float).to_numpy(), axis=1)
    imu = pd.DataFrame({"t": T, "acc": acc, "gyr": gyr})
    return imu, (tcol.lower()=="t_abs")

def ema_inplace(y, k):
    if k<=1: return y
    for i in range(1,len(y)): y[i] = (y[i] + (k-1)*y[i-1]) / k
    return y

def draw_strip(W, H, t_rel, ts, ys, spans=None, color=(255,255,255), win=6.0, dash=False):
    strip = np.zeros((H,W,3), dtype=np.uint8)
    if ts is None or len(ts)==0: return strip
    t0, t1 = t_rel - win/2, t_rel + win/2
    m = (ts>=t0)&(ts<=t1)
    if not np.any(m): return strip
    xs = ((ts[m]-t0)/(t1-t0)*(W-1)).astype(int)
    yv = ys[m]
    yv = (yv - yv.min()) / (np.ptp(yv)+1e-6)
    yp = (H-1 - yv*(H-1)).astype(int)
    for i in range(1,len(xs)):
        if dash and (i%4<2): continue
        cv2.line(strip, (xs[i-1], yp[i-1]), (xs[i], yp[i]), color, 1)
    # draw spans as magenta brackets
    if spans:
        for s,e in spans:
            if e<t0 or s>t1: continue
            x0 = int((max(s,t0)-t0)/(t1-t0)*(W-1))
            x1 = int((min(e,t1)-t0)/(t1-t0)*(W-1))
            cv2.line(strip, (x0,0), (x0,H-1), (255,0,255), 2)
            cv2.line(strip, (x1,0), (x1,H-1), (255,0,255), 2)
    Xc = int((t_rel - t0)/(t1-t0)*(W-1))
    cv2.line(strip, (Xc,0), (Xc,H-1), (0,0,255), 1)
    return strip

# --------- spans from per-frame flags ---------
def flags_to_spans(times, flags):
    spans=[]; in_span=False; s=None
    for t,f in zip(times, flags):
        if f and not in_span: s=t; in_span=True
        elif not f and in_span: spans.append((s, prev_t)); in_span=False
        prev_t=t
    if in_span: spans.append((s, times[-1]))
    return spans

def clear_span_at_time(times, flags, t_rel, tol):
    spans = flags_to_spans(times, flags)
    for s,e in spans:
        if abs(t_rel-s)<tol or abs(t_rel-e)<tol or (t_rel>=s and t_rel<=e):
            m = (times>=s)&(times<=e)
            flags[m]=False
            return True
    return False

# --------- main ---------
def main():
    args = parse_args()

    sess = Path(args.session_dir)
    if not sess.is_dir(): sys.exit(f"[err] not a directory: {sess}")

    # Determine video path: prefer session/video.mov, else parent/video-*.mov
    if args.video:
        video_path = Path(args.video)
    else:
        session_video = sess/"video.mov"
        if session_video.exists():
            video_path = session_video
        else:
            # Try to find video-*.mov in parent
            parent = sess.parent
            stem = sess.name[len("session-"):] if sess.name.startswith("session-") else None
            candidate = parent / f"video-{stem}.mov" if stem else None
            if candidate and candidate.exists():
                video_path = candidate
            else:
                sys.exit(f"[err] video not found: {session_video} or {candidate}")

    # Try to find original imu-*.csv and video-*.mov in parent directory (chew/)
    orig_imu = None
    orig_video = None
    parent = sess.parent
    stem = sess.name[len("session-"):] if sess.name.startswith("session-") else None
    if stem:
        imu_candidate = parent / f"imu-{stem}.csv"
        video_candidate = parent / f"video-{stem}.mov"
        if imu_candidate.exists():
            orig_imu = imu_candidate
        if video_candidate.exists():
            orig_video = video_candidate

    # No IMU waveform/strips: video only

    # pre-load existing chew flags (optional)
    existing = sess/"chew_labels.csv"
    existing_flags = None
    if existing.exists():
        try:
            E = pd.read_csv(existing)
            if {"t_rel","chew"}.issubset(E.columns):
                existing_flags = E[["t_rel","chew"]].astype({"t_rel":float,"chew":int}).values
        except Exception:
            pass

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened(): sys.exit(f"[err] could not open video: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or -1

    # timeline at frame resolution
    frame_times = np.arange(n_frames, dtype=np.float64) / fps
    chew_flags = np.zeros(n_frames, dtype=bool)

    # restore existing flags by nearest-frame mapping
    if existing_flags is not None:
        tr = np.array([row[0] for row in existing_flags], dtype=float)
        ch = np.array([row[1] for row in existing_flags], dtype=int)
        # map: for each saved t_rel, set nearest frame's flag = chew
        idx = np.clip(np.round(tr*fps).astype(int), 0, n_frames-1)
        chew_flags[idx] = ch.astype(bool)


    def save_csv():
        # save only frames where chew=True (compact)
        m = chew_flags
        out = pd.DataFrame({"t_rel": frame_times[m], "chew": np.ones(m.sum(), dtype=int)})
        out_path = sess/"chew_labels.csv"
        out.to_csv(out_path, index=False, float_format="%.6f")
        print(f"[info] saved {out_path}  rows={len(out)}")

    def finalize_prompt():
        try:
            resp = input("\nAre chews finalized for this session? Move original imu/video into session folder? [y/N]: ").strip().lower()
            return resp == 'y'
        except Exception:
            return False

    def move_originals():
        import shutil
        moved = False
        if orig_imu and not (sess/"imu.csv").exists():
            shutil.move(str(orig_imu), str(sess/"imu.csv"))
            print(f"[info] moved {orig_imu} -> {sess/'imu.csv'}")
            moved = True
        if orig_video and not (sess/"video.mov").exists():
            shutil.move(str(orig_video), str(sess/"video.mov"))
            print(f"[info] moved {orig_video} -> {sess/'video.mov'}")
            moved = True
        if not moved:
            print("[info] No original files to move or already present.")

    def handle_exit(*_):
        save_csv()
        cv2.destroyAllWindows()
        # Only prompt if originals exist
        if orig_imu or orig_video:
            if finalize_prompt():
                move_originals()
            else:
                print("[info] Not finalized; originals left in place.")
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_exit); signal.signal(signal.SIGTERM, handle_exit)

    # UI state
    playing=False; idx=0; show_help=True; span_start=None
    playback_fps = 12.0  # Target playback FPS when playing
    min_playback_fps = 1.0
    max_playback_fps = 120.0
    frame_skip = 1  # How many frames to skip during playback (computed below)
    def update_frame_skip():
        nonlocal frame_skip
        if fps > playback_fps:
            frame_skip = int(round(fps / playback_fps))
        else:
            frame_skip = 1
    update_frame_skip()


    try:
        while True:
            if playing:
                # Skip frames to target playback_fps
                idx = min(idx + frame_skip, n_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                save_csv()
                break
            t_rel = idx / fps

            # Video only, overlays below
            combo = frame.copy()
            h, w = combo.shape[:2]

            # Timeline bar (full video duration)
            bar_h = 24
            bar_y0 = h - bar_h - 8
            bar_y1 = h - 8
            cv2.rectangle(combo, (0, bar_y0), (w, bar_y1), (40,40,40), -1)
            # Draw chew spans as magenta blocks
            spans = flags_to_spans(frame_times, chew_flags)
            for s, e in spans:
                x0 = int(np.clip(s / frame_times[-1], 0, 1) * w)
                x1 = int(np.clip(e / frame_times[-1], 0, 1) * w)
                cv2.rectangle(combo, (x0, bar_y0), (x1, bar_y1), (255,0,255), -1)
            # Draw player head (current frame)
            x_head = int(np.clip(t_rel / frame_times[-1], 0, 1) * w)
            cv2.line(combo, (x_head, bar_y0), (x_head, bar_y1), (0,255,255), 2)
            # Draw start/end marker if marking a span
            if span_start is not None:
                x_start = int(np.clip((span_start / fps) / frame_times[-1], 0, 1) * w)
                cv2.line(combo, (x_start, bar_y0), (x_start, bar_y1), (0,255,0), 2)
                cv2.putText(combo, "CHEW START", (x_start+8, bar_y0-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2, cv2.LINE_AA)

            # Info overlays
            cv2.putText(combo, f"t={t_rel:7.3f}s  fps={fps:.2f}  playback={playback_fps:.1f}x", (12, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)
            if show_help:
                lines = [
                    "SPACE: play/pause   A/D: frame -/+    F/G: -/+1s",
                    "C: start/end chew span     X: clear span under cursor",
                    "I: toggle help             Q/ESC: save & quit",
                    "[/]: decrease/increase playback speed"
                ]
                y = 60
                for L in lines:
                    cv2.putText(combo, L, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2, cv2.LINE_AA)
                    y += 28

            cv2.imshow("review", combo)
            key = cv2.waitKeyEx(1 if playing else 25) & 0xFF

            if key in (ord('q'), 27):
                save_csv()
                cv2.destroyAllWindows()
                # Only prompt if originals exist
                if orig_imu or orig_video:
                    if finalize_prompt():
                        move_originals()
                    else:
                        print("[info] Not finalized; originals left in place.")
                break
            elif key == ord(' '):
                playing = not playing
            elif key == ord('a'):
                idx = max(0, idx-1)
            elif key == ord('d'):
                idx = min(n_frames-1, idx+1)
            elif key == ord('f'):
                idx = max(0, idx-int(fps))
            elif key == ord('g'):
                idx = min(n_frames-1, idx+int(fps))
            elif key == ord('i'):
                show_help = not show_help

            elif key == ord('c'):
                if span_start is None:
                    span_start = idx
                    print(f"[info] chew start @ {idx/fps:.3f}s")
                else:
                    s = min(span_start, idx); e = max(span_start, idx)
                    chew_flags[s:e+1] = True
                    print(f"[info] chew span set [{s/fps:.3f}, {e/fps:.3f}]")
                    span_start = None

            elif key == ord('x'):
                # clear span the cursor is inside (or boundary)
                tol = 0.25  # seconds
                if clear_span_at_time(frame_times, chew_flags, t_rel, tol):
                    print("[info] span cleared")
                else:
                    print("[info] no span at cursor")

            elif key == ord('['):
                # Decrease playback speed (halve, but not below min)
                playback_fps = max(min_playback_fps, playback_fps / 2)
                update_frame_skip()
                print(f"[info] playback speed: {playback_fps:.1f}x")
            elif key == ord(']'):
                # Increase playback speed (double, but not above max)
                playback_fps = min(max_playback_fps, playback_fps * 2)
                update_frame_skip()
                print(f"[info] playback speed: {playback_fps:.1f}x")

            # If paused and user navigates, don't skip frames
            if not playing and key in (ord('a'), ord('d'), ord('f'), ord('g')):
                frame_skip = 1
            elif playing:
                update_frame_skip()

    finally:
        save_csv()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
import argparse, subprocess, sys
from pathlib import Path
import pandas as pd

def seed_empty_chew_csv(folder: Path):
    out = folder / "chew_labels.csv"
    if not out.exists():
        pd.DataFrame(columns=["t_rel","chew"]).to_csv(out, index=False)
        print(f"[info] seeded empty {out}")

def run_reviewer(session_dir, reviewer="review_chews.py", offset=None, win=6.0, imu_smooth=0.25):
    args = [sys.executable, reviewer, "--session-dir", str(session_dir), "--win", str(win), "--imu-smooth", str(imu_smooth)]
    if offset is not None: args += ["--offset", str(offset)]
    print(f"[info] launching reviewer: {' '.join(args)}")
    subprocess.run(args, check=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Directory with subfolders 'chew/' and/or 'not-chew/' (or 'null/')")
    ap.add_argument("--reviewer", default="review_chews.py")
    ap.add_argument("--offset", type=float, default=None)
    ap.add_argument("--win", type=float, default=6.0)
    ap.add_argument("--imu-smooth", type=float, default=0.25)
    args = ap.parse_args()

    root = Path(args.input_dir)
    if not root.exists():
        sys.exit(f"[err] input-dir not found: {root}")


    def process_chew_dir(label_dir):
        if not label_dir.is_dir():
            return
        # Only process imu-*.csv and video-*.mov not already in a session-* folder
        imu_files = [f for f in label_dir.glob("imu-*.csv") if not (label_dir / f"session-{f.stem[len('imu-'):]}").exists()]
        for imu_file in imu_files:
            stem = imu_file.stem[len("imu-"):]
            video_file = label_dir / f"video-{stem}.mov"
            if not video_file.exists():
                print(f"[warn] missing {video_file}; skipping pair for {imu_file}")
                continue
            session_dir = label_dir / f"session-{stem}"
            session_dir.mkdir(exist_ok=True)
            # Only seed chew_labels.csv, do not move or symlink files
            seed_empty_chew_csv(session_dir)
            run_reviewer(session_dir, reviewer=args.reviewer, offset=args.offset, win=args.win, imu_smooth=args.imu_smooth)

    def process_notchew_dir(label_dir):
        if not label_dir.is_dir():
            return
        # Only process imu-*.csv and video-*.mov not already in a session-* folder
        imu_files = [f for f in label_dir.glob("imu-*.csv") if not (label_dir / f"session-{f.stem[len('imu-'):]}").exists()]
        for imu_file in imu_files:
            stem = imu_file.stem[len("imu-"):]
            video_file = label_dir / f"video-{stem}.mov"
            if not video_file.exists():
                print(f"[warn] missing {video_file}; skipping pair for {imu_file}")
                continue
            session_dir = label_dir / f"session-{stem}"
            session_dir.mkdir(exist_ok=True)
            seed_empty_chew_csv(session_dir)
            # Move the files into the session folder
            import shutil
            try:
                shutil.move(str(imu_file), str(session_dir / "imu.csv"))
                shutil.move(str(video_file), str(session_dir / "video.mov"))
                print(f"[info] moved {imu_file} and {video_file} to {session_dir}")
            except Exception as e:
                print(f"[err] failed to move files for {stem}: {e}")

    # Process chew directory (run reviewer)
    process_chew_dir(root / "chew")
    # Process not-chew directory (just seed empty csv)
    process_notchew_dir(root / "not-chew")

    # For null, just seed empty file (no session pairs expected)
    null_dir = root / "null"
    if null_dir.is_dir():
        seed_empty_chew_csv(null_dir)
        print(f"[info] null/ labeled as all non-chew (empty file is fine)")

if __name__ == "__main__":
    main()
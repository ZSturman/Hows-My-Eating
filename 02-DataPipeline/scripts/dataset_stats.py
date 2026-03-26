import os
import argparse
import numpy as np
import pandas as pd

# ============================================================
# THRESHOLDS (SECONDS)
# ============================================================

HARD_CHEW = 10 * 60        # 10 min
HARD_NON  = 30 * 60        # 30 min

PRAC_CHEW = 45 * 60        # 45 min
PRAC_NON  = 2 * 60 * 60    # 2 hours

IDEAL_CHEW = 3 * 60 * 60   # 3 hours
IDEAL_NON  = 10 * 60 * 60  # 10 hours

# ============================================================
# HELPERS
# ============================================================

def fmt(seconds):
    return f"{seconds:.1f}s | {seconds/60:.2f}m | {seconds/3600:.2f}h"

def detect_fs(t):
    dt = np.diff(t)
    dt = dt[(dt > 0) & (dt < np.percentile(dt, 95))]
    return 1.0 / np.median(dt)

# ============================================================
# CORE STATS FUNCTION (CSV ONLY)
# ============================================================ 

def compute_stats(input_dir, label_col="chewing_soft", timestamp_col=None):
    total_chew = 0.0
    total_non = 0.0

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".csv"):
            continue

        path = os.path.join(input_dir, fname)
        print(f"Processing: {fname}")

        df = pd.read_csv(path)

        # -------- Timestamp column --------
        ts_col = timestamp_col
        if ts_col is None:
            for c in ["timestamp", "time", "ts", "datetime"]:
                if c in df.columns:
                    ts_col = c
                    break
        if ts_col is None:
            raise ValueError(f"No timestamp column in {fname}")

        # -------- Time base --------
        if not np.issubdtype(df[ts_col].dtype, np.number):
            t = pd.to_datetime(df[ts_col]).astype("int64") / 1e9
        else:
            t = df[ts_col].values.astype(float)

        fs = detect_fs(t)
        dt = 1.0 / fs

        chew_soft = df[label_col].values.astype(float)

        chew_mask = chew_soft > 0.5
        chew_samples = chew_mask.sum()
        non_samples = len(chew_mask) - chew_samples

        total_chew += chew_samples * dt
        total_non  += non_samples * dt

    return total_chew, total_non

# ============================================================
# REPORT
# ============================================================

def report(chew, non):
    total = chew + non
    chew_ratio = chew / total if total > 0 else 0
    non_ratio  = non / total if total > 0 else 0

    print("\n================ DATASET STATS ================")
    print(f"Total time:   {fmt(total)}")
    print(f"Chewing:      {fmt(chew)}  ({chew_ratio*100:.2f}%)")
    print(f"Non-chewing:  {fmt(non)}   ({non_ratio*100:.2f}%)")
    print("================================================\n")

    def remaining(cur, target):
        return max(target - cur, 0.0)

    levels = [
        ("HARD MINIMUM", HARD_CHEW, HARD_NON),
        ("PRACTICAL",    PRAC_CHEW, PRAC_NON),
        ("IDEAL",       IDEAL_CHEW, IDEAL_NON),
    ]

    for name, chew_t, non_t in levels:
        r_chew = remaining(chew, chew_t)
        r_non  = remaining(non, non_t)

        print(name + ":")
        if r_chew == 0 and r_non == 0:
            print("  ✓ Already satisfied.\n")
        else:
            print(f"  Chewing:     {'OK' if r_chew==0 else 'need +' + fmt(r_chew)}")
            print(f"  Non-chewing: {'OK' if r_non==0 else 'need +' + fmt(r_non)}\n")

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Chewing vs Non-chewing dataset statistics (CSV only)")
    parser.add_argument("--input_dir", required=True, help="Directory of input CSV files")
    parser.add_argument("--label_col", default="chewing_soft")
    parser.add_argument("--timestamp_col", default=None)

    args = parser.parse_args()

    chew_sec, non_sec = compute_stats(
        input_dir=args.input_dir,
        label_col=args.label_col,
        timestamp_col=args.timestamp_col,
    )

    report(chew_sec, non_sec)

if __name__ == "__main__":
    main()
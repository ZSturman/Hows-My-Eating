import os
import argparse
import numpy as np
import pandas as pd
from scipy.signal import welch
import shutil
import json

# Combined transform + feature extraction for Chew Sense
# Produces transformed CSVs (with `chewing_soft`) and feature arrays (`X.npy`, `y.npy`).


def process_csv(
    input_csv_path,
    output_csv_path,
    label_col="label",
    timestamp_col=None,
    transition_sec=0.6,
    long_chew_sec=3.0,
    long_ramp_sec=1.5,
):
    """
    Read a CSV, compute a soft chewing label `chewing_soft` and write out a transformed CSV.
    """

    df = pd.read_csv(input_csv_path)

    # Auto-detect timestamp column
    if timestamp_col is None:
        candidates = ["timestamp", "time", "ts", "datetime"]
        found = None
        for c in candidates:
            if c in df.columns:
                found = c
                break
        if found is None:
            raise ValueError(f"No timestamp column found in {input_csv_path}")
        timestamp_col = found

    # Detect sampling rate
    if not np.issubdtype(df[timestamp_col].dtype, np.number):
        t = pd.to_datetime(df[timestamp_col]).astype("int64") / 1e9
    else:
        t = df[timestamp_col].astype(float).values

    dt = np.diff(t)
    dt = dt[(dt > 0) & (dt < np.percentile(dt, 95))]
    sampling_rate_hz = 1.0 / np.median(dt)

    # Prepare labels
    labels = df[label_col].astype(int).values
    n = len(labels)

    soft_ramp_samples = int(transition_sec * sampling_rate_hz)
    long_chew_samples = int(long_chew_sec * sampling_rate_hz)
    long_ramp_samples = int(long_ramp_sec * sampling_rate_hz)

    chewing_soft = np.zeros(n)

    # Find chew segments
    segments = []
    in_segment = False

    for i in range(n):
        if labels[i] == 1 and not in_segment:
            start = i
            in_segment = True
        elif labels[i] == 0 and in_segment:
            end = i
            segments.append((start, end))
            in_segment = False

    if in_segment:
        segments.append((start, n))

    # Apply soft label logic
    for start, end in segments:
        length = end - start

        # Short chews: symmetric ramp up/down
        if length < long_chew_samples:
            ramp = max(length // 2, 1)

            for i in range(start, start + ramp):
                chewing_soft[i] = (i - start) / ramp

            for i in range(start + ramp, end):
                chewing_soft[i] = (end - i) / ramp

        else:
            ramp = min(long_ramp_samples, length // 2)
            ramp = max(ramp, 1)

            for i in range(start, start + ramp):
                chewing_soft[i] = (i - start) / ramp

            for i in range(start + ramp, end - ramp):
                chewing_soft[i] = 1.0

            for i in range(end - ramp, end):
                chewing_soft[i] = (end - i) / ramp

    df["chewing_soft"] = chewing_soft
    df.to_csv(output_csv_path, index=False)


def process_csv_directory(
    input_dir,
    output_dir,
    postfix="_transformed",
    label_col="label",
    timestamp_col=None,
    transition_sec=0.6,
    long_chew_sec=3.0,
    long_ramp_sec=1.5,
):
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".csv"):
            continue

        input_path = os.path.join(input_dir, filename)

        base, ext = os.path.splitext(filename)
        output_filename = f"{base}{postfix}{ext}"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing transform: {filename}")

        process_csv(
            input_csv_path=input_path,
            output_csv_path=output_path,
            label_col=label_col,
            timestamp_col=timestamp_col,
            transition_sec=transition_sec,
            long_chew_sec=long_chew_sec,
            long_ramp_sec=long_ramp_sec,
        )

        # After successful transformation, move the original CSV into
        # a `transformed` subdirectory inside the input directory.
        transformed_dir = os.path.join(input_dir, "transformed")
        os.makedirs(transformed_dir, exist_ok=True)

        dest_path = os.path.join(transformed_dir, filename)
        try:
            # Only move when source and destination differ
            if os.path.abspath(input_path) != os.path.abspath(dest_path):
                shutil.move(input_path, dest_path)
                print(f"Moved original CSV to: {dest_path}")
        except Exception as e:
            print(f"Warning: failed to move {input_path} to {dest_path}: {e}")

    print("✅ CSV transformation complete.")


# -----------------------------
# Feature extraction utilities
# -----------------------------


def accel_magnitude(ax, ay, az):
    return np.sqrt(ax**2 + ay**2 + az**2)


def rms(x):
    return np.sqrt(np.mean(x**2))


def zero_crossing_rate(x):
    return np.mean(np.diff(np.signbit(x)))


def jerk(x):
    return np.diff(x, prepend=x[0])


def bandpower(x, fs, fmin=1.0, fmax=3.0):
    f, Pxx = welch(x, fs=fs, nperseg=min(256, len(x)))
    mask = (f >= fmin) & (f <= fmax)
    if mask.sum() == 0:
        return 0.0
    return np.trapz(Pxx[mask], f[mask])


def spectral_centroid(x, fs):
    f, Pxx = welch(x, fs=fs, nperseg=min(256, len(x)))
    denom = np.sum(Pxx)
    if denom == 0:
        return 0.0
    return np.sum(f * Pxx) / denom


FEATURE_NAMES = [
    "mean_accel_mag",
    "var_accel_mag",
    "rms_accel_mag",
    "mean_gyro_mag",
    "rms_gyro_mag",
    "rms_jerk",
    "zcr_accel_mag",
    "chew_bandpower_1_3hz",
    "bandpower_0_8_1_5hz",
    "bandpower_2_4hz",
    "spectral_centroid",
    "spectral_rolloff_0_85",
]


def extract_features(window, fs):
    ax = window["ax"].values
    ay = window["ay"].values
    az = window["az"].values

    gx = window.get("gx")
    gy = window.get("gy")
    gz = window.get("gz")

    # If gyro missing, use zeros
    if gx is None or gy is None or gz is None:
        gx = np.zeros_like(ax)
        gy = np.zeros_like(ay)
        gz = np.zeros_like(az)
    else:
        gx = gx.values
        gy = gy.values
        gz = gz.values

    amag = accel_magnitude(ax, ay, az)
    gmag = accel_magnitude(gx, gy, gz)

    j = jerk(amag)

    # Basic stats
    mean_acc = np.mean(amag)
    var_acc = np.var(amag)
    rms_acc = rms(amag)
    mean_g = np.mean(gmag)
    rms_g = rms(gmag)
    rms_j = rms(j)
    zcr_acc = zero_crossing_rate(amag)

    # Frequency-domain features
    chew_bp = bandpower(amag, fs, fmin=1.0, fmax=3.0)
    bp_0_8_1_5 = bandpower(amag, fs, fmin=0.8, fmax=1.5)
    bp_2_4 = bandpower(amag, fs, fmin=2.0, fmax=4.0)
    spec_cent = spectral_centroid(amag, fs)

    # Spectral rolloff at 0.85
    f, Pxx = welch(amag, fs=fs, nperseg=min(256, len(amag)))
    cumsum = np.cumsum(Pxx)
    if cumsum[-1] == 0:
        spec_rolloff = 0.0
    else:
        thresh = 0.85 * cumsum[-1]
        idx = np.searchsorted(cumsum, thresh)
        if idx >= len(f):
            idx = len(f) - 1
        spec_rolloff = f[idx]

    features = [
        mean_acc,
        var_acc,
        rms_acc,
        mean_g,
        rms_g,
        rms_j,
        zcr_acc,
        chew_bp,
        bp_0_8_1_5,
        bp_2_4,
        spec_cent,
        spec_rolloff,
    ]

    return features


def detect_sampling_rate(t):
    dt = np.diff(t)
    dt = dt[(dt > 0) & (dt < np.percentile(dt, 95))]
    return 1.0 / np.median(dt)


def process_features_directory(
    input_dir,
    output_dir,
    window_sec=0.75,
    step_sec=0.1,
    label_col="chewing_soft",
    timestamp_col=None,
):
    os.makedirs(output_dir, exist_ok=True)

    X_all = []
    y_all = []

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".csv"):
            continue

        path = os.path.join(input_dir, filename)
        print("Processing features:", filename)

        df = pd.read_csv(path)

        # Auto-detect timestamp per file
        ts_col = timestamp_col
        if ts_col is None:
            for c in ["timestamp", "time", "ts", "datetime"]:
                if c in df.columns:
                    ts_col = c
                    break
            if ts_col is None:
                raise ValueError(f"No timestamp column in {filename}")

        # Sampling rate
        if not np.issubdtype(df[ts_col].dtype, np.number):
            t = pd.to_datetime(df[ts_col]).astype("int64") / 1e9
        else:
            t = df[ts_col].astype(float).values

        fs = detect_sampling_rate(t)

        window_samples = int(window_sec * fs)
        step_samples = int(step_sec * fs)

        for start in range(0, len(df) - window_samples, step_samples):
            end = start + window_samples
            w = df.iloc[start:end]

            feats = extract_features(w, fs)
            X_all.append(feats)

            y_all.append(w[label_col].mean())

    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.float32)

    # Save outputs
    np.save(os.path.join(output_dir, "X.npy"), X)
    np.save(os.path.join(output_dir, "y.npy"), y)

    with open(os.path.join(output_dir, "feature_names.txt"), "w") as f:
        for name in FEATURE_NAMES:
            f.write(name + "\n")

    print("✅ Feature generation complete")
    print("X shape:", X.shape)
    print("y shape:", y.shape)


def export_test_json(input_dir, output_path="test.json", window_sec=0.75, step_sec=0.1, label_col="chewing_soft", timestamp_col=None):
    data = {"chewing": [], "not-chewing": []}

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".csv"):
            continue

        path = os.path.join(input_dir, filename)
        print("Processing test features:", filename)

        df = pd.read_csv(path)

        ts_col = timestamp_col
        if ts_col is None:
            for c in ["timestamp", "time", "ts", "datetime"]:
                if c in df.columns:
                    ts_col = c
                    break
            if ts_col is None:
                raise ValueError(f"No timestamp column in {filename}")

        if not np.issubdtype(df[ts_col].dtype, np.number):
            t = pd.to_datetime(df[ts_col]).astype("int64") / 1e9
        else:
            t = df[ts_col].astype(float).values

        fs = detect_sampling_rate(t)

        window_samples = int(window_sec * fs)
        step_samples = int(step_sec * fs)

        for start in range(0, len(df) - window_samples, step_samples):
            end = start + window_samples
            w = df.iloc[start:end]

            feats = extract_features(w, fs)
            label = w[label_col].mean()

            if label >= 0.5:
                data["chewing"].append(feats)
            else:
                data["not-chewing"].append(feats)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Exported test vectors to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Transform CSVs (chewing_soft) and extract features from transformed CSVs")
    parser.add_argument("--input_dir", required=True, help="Directory of input CSV files")

    parser.add_argument("--csv_output_dir", default="transformed_chew_data", help="Directory for transformed CSVs")
    parser.add_argument("--features_output_dir", default="features_output", help="Directory for features output")

    parser.add_argument("--postfix", default="_transformed", help="Postfix added to transformed CSVs")

    parser.add_argument("--label_col", default="label")
    parser.add_argument("--timestamp_col", default=None)

    parser.add_argument("--transition_sec", type=float, default=0.6)
    parser.add_argument("--long_chew_sec", type=float, default=3.0)
    parser.add_argument("--long_ramp_sec", type=float, default=1.5)

    parser.add_argument("--window_sec", type=float, default=0.75)
    parser.add_argument("--step_sec", type=float, default=0.1)

    parser.add_argument("--export_test_json", action="store_true", help="Export test.json instead of generating X.npy/y.npy")

    args = parser.parse_args()

    # 1) Transform CSVs into csv_output_dir
    process_csv_directory(
        input_dir=args.input_dir,
        output_dir=args.csv_output_dir,
        postfix=args.postfix,
        label_col=args.label_col,
        timestamp_col=args.timestamp_col,
        transition_sec=args.transition_sec,
        long_chew_sec=args.long_chew_sec,
        long_ramp_sec=args.long_ramp_sec,
    )

    # 2) Extract features from transformed CSVs and save into features_output_dir or export test.json
    if args.export_test_json:
        export_test_json(
            input_dir=args.csv_output_dir,
            output_path="test.json",
            window_sec=args.window_sec,
            step_sec=args.step_sec,
            label_col="chewing_soft",
            timestamp_col=args.timestamp_col,
        )
    else:
        process_features_directory(
            input_dir=args.csv_output_dir,
            output_dir=args.features_output_dir,
            window_sec=args.window_sec,
            step_sec=args.step_sec,
            label_col="chewing_soft",
            timestamp_col=args.timestamp_col,
        )


if __name__ == "__main__":
    main()

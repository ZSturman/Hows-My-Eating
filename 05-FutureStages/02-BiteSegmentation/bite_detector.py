"""
Bite Detector - Segment continuous chewing into discrete bite events.

Implements temporal clustering: a "bite" is a contiguous run of frames
above the probability threshold, separated from neighbouring bites by at
least `min_gap_sec` of below-threshold (idle) time. Within each bite,
individual chew strokes are counted by detecting peaks in the chewing
probability signal (or, when provided, in the 1-3 Hz acceleration band-
power signal which is more directly tied to jaw motion at ~1.5 Hz).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class BiteEvent:
    """A single detected bite event."""
    start_time: float  # seconds
    end_time: float    # seconds
    duration: float    # seconds
    confidence: float  # average probability during bite
    chew_count: Optional[int] = None  # estimated chews in this bite


@dataclass
class BiteDetectorConfig:
    """Configuration for bite detection algorithm."""
    min_gap_sec: float = 1.5        # minimum below-threshold gap to split bites
    min_bite_duration: float = 1.0  # minimum bite duration to keep
    probability_threshold: float = 0.5  # threshold for chewing state
    # Chew-stroke counting: jaw motion is ~1.5 Hz, so peaks can't be closer than
    # ~0.4 s. Tunable for slower/faster chewers.
    min_chew_period_sec: float = 0.35


class BiteDetector:
    """Segments continuous chewing probability signals into discrete bites."""

    def __init__(self, config: BiteDetectorConfig | None = None):
        self.config = config or BiteDetectorConfig()

    # ------------------------------------------------------------------
    def detect_bites(
        self,
        timestamps: np.ndarray,
        probabilities: np.ndarray,
        chew_signal: Optional[np.ndarray] = None,
    ) -> List[BiteEvent]:
        """Detect bite events from a chewing-probability signal.

        Args:
            timestamps:    1-D array of frame timestamps in seconds.
            probabilities: 1-D array of chewing probabilities in [0, 1],
                           one per timestamp.
            chew_signal:   Optional 1-D array used for chew-stroke peak
                           counting (e.g. the 1-3 Hz band-power feature).
                           If omitted, peaks are detected in `probabilities`.

        Returns:
            List of `BiteEvent`, one per accepted bite.
        """
        timestamps = np.asarray(timestamps, dtype=float)
        probabilities = np.asarray(probabilities, dtype=float)
        if timestamps.shape != probabilities.shape:
            raise ValueError("timestamps and probabilities must have the same shape")
        if timestamps.size == 0:
            return []

        cfg = self.config
        is_chew = probabilities >= cfg.probability_threshold
        segments = self._find_chewing_segments(timestamps, is_chew)
        merged = self._merge_close_segments(timestamps, segments, cfg.min_gap_sec)

        peak_signal = chew_signal if chew_signal is not None else probabilities
        peak_signal = np.asarray(peak_signal, dtype=float)

        bites: List[BiteEvent] = []
        for start_idx, end_idx in merged:
            duration = float(timestamps[end_idx] - timestamps[start_idx])
            if duration < cfg.min_bite_duration:
                continue
            confidence = float(np.mean(probabilities[start_idx : end_idx + 1]))
            chew_count = self._estimate_chew_count(
                timestamps[start_idx : end_idx + 1],
                peak_signal[start_idx : end_idx + 1],
            )
            bites.append(BiteEvent(
                start_time=float(timestamps[start_idx]),
                end_time=float(timestamps[end_idx]),
                duration=duration,
                confidence=confidence,
                chew_count=chew_count,
            ))
        return bites

    # ------------------------------------------------------------------
    def _find_chewing_segments(
        self,
        timestamps: np.ndarray,
        is_chewing: np.ndarray,
    ) -> List[Tuple[int, int]]:
        """Return inclusive (start_idx, end_idx) pairs for each True run."""
        if is_chewing.size == 0:
            return []
        # Boundaries via diff on padded array.
        padded = np.concatenate(([False], is_chewing, [False]))
        edges = np.diff(padded.astype(np.int8))
        starts = np.where(edges == 1)[0]
        ends = np.where(edges == -1)[0] - 1
        return list(zip(starts.tolist(), ends.tolist()))

    def _merge_close_segments(
        self,
        timestamps: np.ndarray,
        segments: List[Tuple[int, int]],
        min_gap_sec: float,
    ) -> List[Tuple[int, int]]:
        """Merge segments separated by less than `min_gap_sec` of idle time."""
        if not segments:
            return []
        merged = [segments[0]]
        for start, end in segments[1:]:
            prev_start, prev_end = merged[-1]
            gap = timestamps[start] - timestamps[prev_end]
            if gap < min_gap_sec:
                merged[-1] = (prev_start, end)
            else:
                merged.append((start, end))
        return merged

    def _estimate_chew_count(
        self,
        timestamps: np.ndarray,
        signal: np.ndarray,
    ) -> int:
        """Count chew strokes by simple local-maximum peak detection.

        A point i is a peak if signal[i] > signal[i-1] and signal[i] >= signal[i+1]
        and at least `min_chew_period_sec` has elapsed since the last accepted
        peak. This is a deliberately lightweight rule — robust enough for
        ~1.5 Hz jaw motion without pulling in scipy.signal.find_peaks.
        """
        if signal.size < 3:
            return 0
        cfg = self.config
        last_t = -np.inf
        count = 0
        # Mean threshold guards against counting noise-floor wiggles
        # in long mostly-flat segments.
        threshold = float(np.mean(signal))
        for i in range(1, signal.size - 1):
            if signal[i] <= threshold:
                continue
            if signal[i] <= signal[i - 1] or signal[i] < signal[i + 1]:
                continue
            t = float(timestamps[i])
            if t - last_t < cfg.min_chew_period_sec:
                continue
            count += 1
            last_t = t
        return count


def main():
    """CLI entry point for bite detection."""
    import argparse
    import csv
    import json
    from dataclasses import asdict
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Detect bites from chewing log")
    parser.add_argument("input_csv", help="Path to chewing log CSV (timestamp,probability[,chew_signal])")
    parser.add_argument("--min-gap", type=float, default=1.5,
                        help="Minimum below-threshold gap between bites (seconds)")
    parser.add_argument("--min-duration", type=float, default=1.0,
                        help="Minimum bite duration to keep (seconds)")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Chewing probability threshold")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    timestamps: list[float] = []
    probs: list[float] = []
    chew_sig: list[float] = []
    with open(args.input_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(float(row["timestamp"]))
            probs.append(float(row["probability"]))
            if "chew_signal" in row and row["chew_signal"] != "":
                chew_sig.append(float(row["chew_signal"]))

    detector = BiteDetector(BiteDetectorConfig(
        min_gap_sec=args.min_gap,
        min_bite_duration=args.min_duration,
        probability_threshold=args.threshold,
    ))
    bites = detector.detect_bites(
        np.asarray(timestamps),
        np.asarray(probs),
        np.asarray(chew_sig) if chew_sig else None,
    )

    payload = {
        "input": args.input_csv,
        "n_bites": len(bites),
        "total_chew_count": sum(b.chew_count or 0 for b in bites),
        "bites": [asdict(b) for b in bites],
    }
    text = json.dumps(payload, indent=2)
    if args.output:
        Path(args.output).write_text(text)
        print(f"Wrote {len(bites)} bites -> {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()

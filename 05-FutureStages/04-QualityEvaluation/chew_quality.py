"""
Chew Quality Evaluator - Assess chewing behavior quality.

Scores three dimensions per the design doc:
  - pace          (30%) — inter-bite spacing vs. target window
  - thoroughness  (40%) — chews-per-bite vs. 20-30 guideline
  - rhythm        (30%) — consistency of inter-bite spacing

A 0-100 overall score is reported alongside per-dimension ratings and
remediation recommendations. Thresholds are tunable via
`QualityEvaluatorConfig` so future field-test data can recalibrate them
without touching this module.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional


class QualityRating(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    NEEDS_IMPROVEMENT = "needs_improvement"


def _score_to_rating(score: float) -> QualityRating:
    if score >= 85:
        return QualityRating.EXCELLENT
    if score >= 70:
        return QualityRating.GOOD
    if score >= 50:
        return QualityRating.FAIR
    return QualityRating.NEEDS_IMPROVEMENT


@dataclass
class ChewQualityMetrics:
    """Quality metrics for a single meal or eating session."""
    avg_chews_per_bite: float
    avg_bite_duration: float
    eating_pace_rating: QualityRating

    rushed_bites_percent: float
    well_chewed_percent: float
    thoroughness_rating: QualityRating

    pace_consistency: float
    mindful_pauses: int
    rhythm_rating: QualityRating

    overall_score: float
    overall_rating: QualityRating
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QualityEvaluatorConfig:
    """Configuration for quality evaluation."""
    target_chews_min: int = 20
    target_chews_max: int = 30
    rushed_threshold: int = 5
    target_pace_min: float = 5.0    # seconds between bite starts
    target_pace_max: float = 15.0
    mindful_pause_sec: float = 30.0  # gap that counts as a mindful pause

    weight_pace: float = 0.3
    weight_thoroughness: float = 0.4
    weight_rhythm: float = 0.3


class ChewQualityEvaluator:
    """Evaluate chewing quality from a list of `BiteEvent`-like records."""

    def __init__(self, config: QualityEvaluatorConfig | None = None):
        self.config = config or QualityEvaluatorConfig()

    # ------------------------------------------------------------------
    def evaluate_meal(self, meal_metrics, bites: List) -> ChewQualityMetrics:
        """Evaluate quality of a meal's chewing behavior.

        Args:
            meal_metrics: Optional summary object. May expose
                `meal_duration` (seconds). Pass `None` to derive from bites.
            bites: Iterable of objects with at least
                `start_time`, `end_time`, `duration`, `chew_count`.
        """
        bites = list(bites)
        if not bites:
            return ChewQualityMetrics(
                avg_chews_per_bite=0.0,
                avg_bite_duration=0.0,
                eating_pace_rating=QualityRating.NEEDS_IMPROVEMENT,
                rushed_bites_percent=0.0,
                well_chewed_percent=0.0,
                thoroughness_rating=QualityRating.NEEDS_IMPROVEMENT,
                pace_consistency=0.0,
                mindful_pauses=0,
                rhythm_rating=QualityRating.NEEDS_IMPROVEMENT,
                overall_score=0.0,
                overall_rating=QualityRating.NEEDS_IMPROVEMENT,
                recommendations=["No bites detected — try a longer recording."],
            )

        cfg = self.config

        # ---- Thoroughness (chews per bite) -------------------------------
        chew_counts = [int(b.chew_count or 0) for b in bites]
        avg_chews = statistics.mean(chew_counts) if chew_counts else 0.0
        avg_duration = statistics.mean([float(b.duration) for b in bites])
        rushed = sum(1 for c in chew_counts if c < cfg.rushed_threshold)
        well = sum(1 for c in chew_counts if c >= cfg.target_chews_min)
        rushed_pct = 100.0 * rushed / len(bites)
        well_pct = 100.0 * well / len(bites)
        thoroughness_score = self._score_thoroughness(chew_counts)
        thoroughness_rating = _score_to_rating(thoroughness_score)

        # ---- Pace (inter-bite gaps) --------------------------------------
        starts = sorted(float(b.start_time) for b in bites)
        gaps = [starts[i] - starts[i - 1] for i in range(1, len(starts))]
        pace_score = self._score_pace(gaps) if gaps else 50.0
        pace_rating = _score_to_rating(pace_score)

        # ---- Rhythm (gap consistency + mindful pauses) -------------------
        rhythm_score, mindful_pauses = self._score_rhythm(gaps)
        rhythm_rating = _score_to_rating(rhythm_score)
        pace_consistency = max(0.0, min(1.0, rhythm_score / 100.0))

        overall = (
            cfg.weight_pace * pace_score
            + cfg.weight_thoroughness * thoroughness_score
            + cfg.weight_rhythm * rhythm_score
        )
        overall_rating = _score_to_rating(overall)

        recommendations = self._generate_recommendations(
            pace_rating, thoroughness_rating, rhythm_rating
        )

        return ChewQualityMetrics(
            avg_chews_per_bite=float(avg_chews),
            avg_bite_duration=float(avg_duration),
            eating_pace_rating=pace_rating,
            rushed_bites_percent=float(rushed_pct),
            well_chewed_percent=float(well_pct),
            thoroughness_rating=thoroughness_rating,
            pace_consistency=float(pace_consistency),
            mindful_pauses=int(mindful_pauses),
            rhythm_rating=rhythm_rating,
            overall_score=float(overall),
            overall_rating=overall_rating,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    def _score_thoroughness(self, chew_counts: Iterable[int]) -> float:
        """Score 0-100 against the 20-30 chews-per-bite guideline.

        Each bite contributes a per-bite score; the meal score is the mean.
        Bites with chew_count == 0 (no per-bite count) are skipped to avoid
        penalising sessions where chew counting was unavailable.
        """
        cfg = self.config
        per_bite: List[float] = []
        for c in chew_counts:
            if c <= 0:
                continue
            if cfg.target_chews_min <= c <= cfg.target_chews_max:
                per_bite.append(100.0)
            elif c < cfg.target_chews_min:
                # Linear from 0 chews -> 0 to target_chews_min -> 95
                per_bite.append(95.0 * c / cfg.target_chews_min)
            else:
                # Over-chewing: gentle penalty above target_max
                excess = c - cfg.target_chews_max
                per_bite.append(max(60.0, 100.0 - 1.5 * excess))
        if not per_bite:
            return 50.0
        return float(statistics.mean(per_bite))

    def _score_pace(self, gaps: List[float]) -> float:
        """Score 0-100 based on whether inter-bite gaps fall in the target band."""
        cfg = self.config
        if not gaps:
            return 50.0
        in_band = 0
        for g in gaps:
            if cfg.target_pace_min <= g <= cfg.target_pace_max:
                in_band += 1
        in_band_pct = 100.0 * in_band / len(gaps)
        # Penalise extreme medians too — eating in 1 s flurries or 60 s gaps.
        median_gap = statistics.median(gaps)
        if median_gap < cfg.target_pace_min:
            penalty = 30.0 * (cfg.target_pace_min - median_gap) / cfg.target_pace_min
        elif median_gap > cfg.target_pace_max:
            penalty = min(30.0, 1.0 * (median_gap - cfg.target_pace_max))
        else:
            penalty = 0.0
        return max(0.0, in_band_pct - penalty)

    def _score_rhythm(self, gaps: List[float]) -> tuple[float, int]:
        """Score consistency of gaps; also count mindful pauses."""
        cfg = self.config
        if len(gaps) < 2:
            return 60.0, 0
        mean_gap = statistics.mean(gaps)
        if mean_gap <= 0:
            return 50.0, 0
        stdev = statistics.pstdev(gaps)
        # Coefficient of variation: 0 = perfectly steady, 1+ = very erratic.
        cv = stdev / mean_gap
        # Map CV in [0, 1] to score [100, 0].
        score = max(0.0, 100.0 * (1.0 - min(1.0, cv)))
        mindful_pauses = sum(1 for g in gaps if g >= cfg.mindful_pause_sec)
        # Reward up to two mindful pauses per meal.
        score = min(100.0, score + min(2, mindful_pauses) * 5.0)
        return score, mindful_pauses

    def _generate_recommendations(
        self,
        pace_rating: QualityRating,
        thoroughness_rating: QualityRating,
        rhythm_rating: QualityRating,
    ) -> List[str]:
        recs: List[str] = []
        weak = {QualityRating.FAIR, QualityRating.NEEDS_IMPROVEMENT}
        if pace_rating in weak:
            recs.append("Slow down — aim for 5-15 seconds between bites.")
        if thoroughness_rating in weak:
            recs.append("Chew each bite more thoroughly — target 20-30 chews per bite.")
        if rhythm_rating in weak:
            recs.append("Keep a steadier rhythm — avoid alternating rushed and idle stretches.")
        if not recs:
            recs.append("Great chewing habits — keep it up.")
        return recs


def main():
    """CLI entry point: take a bite-detector JSON, emit a quality report."""
    import argparse
    import json
    from dataclasses import asdict
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Evaluate chewing quality")
    parser.add_argument("meal_json", help="Path to bite-detector JSON output")
    parser.add_argument("--output", "-o", help="Output quality report path (JSON)")
    args = parser.parse_args()

    payload = json.loads(Path(args.meal_json).read_text())
    raw_bites = payload.get("bites", [])

    @dataclass
    class _Bite:
        start_time: float
        end_time: float
        duration: float
        confidence: float = 0.0
        chew_count: Optional[int] = None

    bites = [_Bite(**{k: b.get(k) for k in ("start_time", "end_time", "duration", "confidence", "chew_count")})
             for b in raw_bites]

    evaluator = ChewQualityEvaluator()
    metrics = evaluator.evaluate_meal(meal_metrics=None, bites=bites)
    out = {
        "input": args.meal_json,
        "n_bites": len(bites),
        "metrics": {
            **{k: v for k, v in asdict(metrics).items() if not isinstance(v, QualityRating)},
            "eating_pace_rating": metrics.eating_pace_rating.value,
            "thoroughness_rating": metrics.thoroughness_rating.value,
            "rhythm_rating": metrics.rhythm_rating.value,
            "overall_rating": metrics.overall_rating.value,
        },
    }
    text = json.dumps(out, indent=2)
    if args.output:
        Path(args.output).write_text(text)
        print(f"Wrote quality report -> {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()

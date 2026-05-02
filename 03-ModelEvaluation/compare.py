"""
Compare the two most recent model registry entries and emit a markdown report.

This is the third stage of the iteration loop:

    [02 train] -> registry entry
    [03 compare] -> markdown delta vs previous entry  <-- you are here
    [02 deploy]  -> ship to Xcode

Reads from `02-DataPipeline/model_registry/runs/`. Writes to
`03-ModelEvaluation/reports/<timestamp>_compare.md`. Returns a verdict
("improved" / "regressed" / "neutral") that the deploy step can gate on.

Usage:
    python 03-ModelEvaluation/compare.py
    python 03-ModelEvaluation/compare.py --baseline <model_id> --candidate <model_id>
    python 03-ModelEvaluation/compare.py --json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_ROOT = REPO_ROOT / "02-DataPipeline" / "model_registry" / "runs"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"

# Higher-is-better metrics. recall/precision/f1/roc_auc/accuracy.
HIGHER_IS_BETTER = ("accuracy", "roc_auc", "precision", "recall", "f1")
# Tolerance below which a delta counts as "neutral" (avoid false alarms from noise).
NEUTRAL_BAND = 0.005
# Splits that block a deploy when they regress. gold_locked is the trustworthy
# external benchmark; field_regression and validation_locked still gate but
# tolerate movement on field-only data.
GATING_SPLITS = ("gold_locked", "validation_locked")


def _load_metrics(entry: Path) -> dict:
    metrics_path = entry / "metrics.json"
    if not metrics_path.exists():
        return {}
    try:
        with open(metrics_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _flatten_metrics(metrics: dict) -> dict[str, dict]:
    """Return {split_name: {metric: value}}, accepting both nested and flat shapes."""
    if not metrics:
        return {}
    # Detect flat-shaped (single split) by presence of a known scalar metric at top.
    if any(key in metrics for key in HIGHER_IS_BETTER):
        return {"all": metrics}
    # Else: assume {split_name: {metric: value}}.
    return {k: v for k, v in metrics.items() if isinstance(v, dict)}


def _list_entries() -> list[Path]:
    if not REGISTRY_ROOT.exists():
        return []
    entries = [p for p in REGISTRY_ROOT.iterdir() if p.is_dir()]
    return sorted(entries, key=lambda p: p.name)


def _resolve_entry(name: Optional[str], entries: list[Path], fallback_index: int) -> Optional[Path]:
    if name:
        match = next((e for e in entries if e.name == name), None)
        if match is None:
            print(f"  registry entry not found: {name}", file=sys.stderr)
        return match
    if abs(fallback_index) > len(entries):
        return None
    return entries[fallback_index]


def _verdict(deltas: dict[str, dict[str, float]]) -> str:
    """Aggregate per-split per-metric deltas into a single verdict.

    Strategy:
      * Only `GATING_SPLITS` (gold_locked, validation_locked) influence the
        verdict — they're stable, ground-truthed, and the only signal we
        trust to block a deploy. If `gold_locked` is present, ONLY
        gold_locked decides.
      * F1 and ROC AUC carry more weight than accuracy because the chewing
        problem is heavily imbalanced — a constant-zero predictor scores
        ~75% accuracy but is useless. A model that gains F1 / AUC wins
        even if accuracy slips.
      * If F1 and AUC both improve beyond NEUTRAL_BAND, the run is
        "improved" regardless of accuracy. If both regress, "regressed".
    """
    if "gold_locked" in deltas:
        gating = {"gold_locked": deltas["gold_locked"]}
    else:
        gating = {k: v for k, v in deltas.items() if k in GATING_SPLITS}
        if not gating:
            gating = deltas  # fallback: no known gating split, use all

    f1_delta = 0.0
    auc_delta = 0.0
    acc_delta = 0.0
    saw_f1 = saw_auc = saw_acc = False
    for split_deltas in gating.values():
        if "f1" in split_deltas and split_deltas["f1"] is not None:
            f1_delta += split_deltas["f1"]; saw_f1 = True
        if "roc_auc" in split_deltas and split_deltas["roc_auc"] is not None:
            auc_delta += split_deltas["roc_auc"]; saw_auc = True
        if "accuracy" in split_deltas and split_deltas["accuracy"] is not None:
            acc_delta += split_deltas["accuracy"]; saw_acc = True

    # If both F1 and AUC are available, they own the verdict on imbalanced
    # data. Accuracy alone cannot block.
    if saw_f1 and saw_auc:
        big_improve = (f1_delta > NEUTRAL_BAND) and (auc_delta > NEUTRAL_BAND)
        big_regress = (f1_delta < -NEUTRAL_BAND) and (auc_delta < -NEUTRAL_BAND)
        if big_improve:
            return "improved"
        if big_regress:
            return "regressed"
        # Mixed signal — fall through to scalar accumulation below.

    any_regressed = False
    any_improved = False
    for split_deltas in gating.values():
        for metric, delta in split_deltas.items():
            if metric not in HIGHER_IS_BETTER or delta is None:
                continue
            if delta < -NEUTRAL_BAND:
                any_regressed = True
            elif delta > NEUTRAL_BAND:
                any_improved = True
    if any_improved and not any_regressed:
        return "improved"
    if any_regressed and not any_improved:
        return "regressed"
    # Both directions present (typical when baseline was a degenerate
    # constant predictor): tie-break with F1 + AUC sum.
    if saw_f1 or saw_auc:
        composite = f1_delta + auc_delta
        if composite > NEUTRAL_BAND:
            return "improved"
        if composite < -NEUTRAL_BAND:
            return "regressed"
    return "neutral"


def compute_comparison(
    baseline: Optional[str] = None,
    candidate: Optional[str] = None,
) -> dict:
    """Compute a comparison report dict between baseline and candidate registry entries."""
    entries = _list_entries()
    if len(entries) < 2 and not (baseline and candidate):
        return {
            "error": "Need at least two registry entries to compare; "
            f"found {len(entries)} in {REGISTRY_ROOT}.",
            "entries_found": [e.name for e in entries],
        }

    candidate_entry = _resolve_entry(candidate, entries, fallback_index=-1)
    baseline_entry = _resolve_entry(baseline, entries, fallback_index=-2)

    if candidate_entry is None or baseline_entry is None:
        return {
            "error": "Could not resolve baseline and candidate entries.",
            "baseline": baseline_entry.name if baseline_entry else None,
            "candidate": candidate_entry.name if candidate_entry else None,
        }

    baseline_metrics = _flatten_metrics(_load_metrics(baseline_entry))
    candidate_metrics = _flatten_metrics(_load_metrics(candidate_entry))

    splits = sorted(set(baseline_metrics) | set(candidate_metrics))
    deltas: dict[str, dict[str, float]] = {}
    table: dict[str, list[dict]] = {}
    activity_table: dict[str, dict[str, list[dict]]] = {}
    for split in splits:
        b = baseline_metrics.get(split, {})
        c = candidate_metrics.get(split, {})
        rows = []
        split_deltas: dict[str, float] = {}
        for metric in HIGHER_IS_BETTER:
            b_val = b.get(metric)
            c_val = c.get(metric)
            delta = (c_val - b_val) if (isinstance(b_val, (int, float)) and isinstance(c_val, (int, float))) else None
            if delta is not None:
                split_deltas[metric] = delta
            rows.append(
                {
                    "metric": metric,
                    "baseline": b_val,
                    "candidate": c_val,
                    "delta": delta,
                }
            )
        deltas[split] = split_deltas
        table[split] = rows

        # Per-activity breakdown when evaluator wrote it
        b_per = b.get("per_activity") if isinstance(b, dict) else None
        c_per = c.get("per_activity") if isinstance(c, dict) else None
        if isinstance(b_per, dict) or isinstance(c_per, dict):
            b_per = b_per or {}
            c_per = c_per or {}
            activities = sorted(set(b_per) | set(c_per))
            per_act: dict[str, list[dict]] = {}
            for activity in activities:
                bp = b_per.get(activity, {})
                cp = c_per.get(activity, {})
                act_rows = []
                for metric in HIGHER_IS_BETTER:
                    b_val = bp.get(metric)
                    c_val = cp.get(metric)
                    delta = (c_val - b_val) if (isinstance(b_val, (int, float)) and isinstance(c_val, (int, float))) else None
                    act_rows.append({
                        "metric": metric, "baseline": b_val, "candidate": c_val, "delta": delta,
                    })
                per_act[activity] = act_rows
            activity_table[split] = per_act

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline": baseline_entry.name,
        "candidate": candidate_entry.name,
        "verdict": _verdict(deltas),
        "table": table,
        "activity_table": activity_table,
    }


def render_markdown(report: dict) -> str:
    if "error" in report:
        return f"# Comparison failed\n\n{report['error']}\n"

    lines: list[str] = []
    lines.append(f"# Model comparison — {report['generated_at']}")
    lines.append("")
    lines.append(f"- **Baseline:**  `{report['baseline']}`")
    lines.append(f"- **Candidate:** `{report['candidate']}`")
    verdict = report["verdict"]
    badge = {"improved": "✅ improved", "regressed": "❌ regressed", "neutral": "➖ neutral"}[verdict]
    lines.append(f"- **Verdict:**   {badge}  (neutral band ±{NEUTRAL_BAND})")
    lines.append("")

    for split, rows in report["table"].items():
        lines.append(f"## Split: `{split}`")
        lines.append("")
        lines.append("| Metric | Baseline | Candidate | Δ |")
        lines.append("|---|---:|---:|---:|")
        for row in rows:
            b = "-" if row["baseline"] is None else f"{row['baseline']:.4f}"
            c = "-" if row["candidate"] is None else f"{row['candidate']:.4f}"
            d = "-" if row["delta"] is None else f"{row['delta']:+.4f}"
            lines.append(f"| {row['metric']} | {b} | {c} | {d} |")
        lines.append("")

        per_act = (report.get("activity_table") or {}).get(split)
        if per_act:
            lines.append(f"### `{split}` — per activity")
            lines.append("")
            lines.append("| Activity | Metric | Baseline | Candidate | Δ |")
            lines.append("|---|---|---:|---:|---:|")
            for activity, act_rows in per_act.items():
                for row in act_rows:
                    b = "-" if row["baseline"] is None else f"{row['baseline']:.4f}"
                    c = "-" if row["candidate"] is None else f"{row['candidate']:.4f}"
                    d = "-" if row["delta"] is None else f"{row['delta']:+.4f}"
                    lines.append(f"| {activity} | {row['metric']} | {b} | {c} | {d} |")
            lines.append("")
    return "\n".join(lines)


def write_report(report: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = REPORTS_DIR / f"{stamp}_compare.md"
    out.write_text(render_markdown(report))
    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--baseline", help="Registry entry id to use as baseline (default: 2nd-newest)")
    parser.add_argument("--candidate", help="Registry entry id to use as candidate (default: newest)")
    parser.add_argument("--json", action="store_true", help="Print JSON only; do not write a markdown report")
    parser.add_argument("--no-write", action="store_true", help="Print markdown to stdout instead of writing a file")
    args = parser.parse_args(argv)

    report = compute_comparison(baseline=args.baseline, candidate=args.candidate)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0 if "error" not in report else 1

    md = render_markdown(report)
    if args.no_write:
        print(md)
    else:
        out = write_report(report)
        print(md)
        print(f"\n📝 Report written: {out}")

    if "error" in report:
        return 1
    # Exit codes: 0 improved/neutral, 2 regressed (so CI / deploy can gate).
    return 2 if report.get("verdict") == "regressed" else 0


if __name__ == "__main__":
    sys.exit(main())

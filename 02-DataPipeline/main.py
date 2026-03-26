"""main.py

Chew Sense end-to-end pipeline.

Happy path (default):
1) Drop new raw CSVs into --input_dir (default: input_dir)
2) Run: python3 main.py

What this script does:
- Validates raw CSVs (fails fast with clear errors)
- Transforms each raw CSV by adding `chewing_soft`
- Writes transformed CSVs into --csv_output_dir
- Moves original raw CSVs into --archive_dir so you know they're processed
- Extracts features from transformed CSVs and writes X.npy/y.npy/feature_names.txt into --features_output_dir
- If --stats is set: prints dataset chewing vs non-chewing time from transformed CSVs
- Prompts to train the model, then prompts to evaluate and/or export CoreML and dump normalization

Notes:
- Existing scripts are kept as-is. Where needed, main.py reuses the same core logic but adds
  orchestration, logging, and flexible paths.
- TODO: export_coreML.py and extra_modules/evaluate.py are currently hard-coded to default paths.
  main.py keeps your existing defaults working, but long-term those scripts could accept CLI args.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch

from scripts import get_features, dataset_stats
from training import train_pytorch


TIMESTAMP_CANDIDATES = ("timestamp", "time", "ts", "datetime")


@dataclass(frozen=True)
class PipelinePaths:
	input_dir: Path
	archive_dir: Path
	csv_output_dir: Path
	features_output_dir: Path
	model_path: Path
	logs_root: Path


class RunLogger:
	def __init__(self, run_dir: Path, log_level: str = "INFO") -> None:
		run_dir.mkdir(parents=True, exist_ok=True)
		self.run_dir = run_dir

		self.logger = logging.getLogger("chewsense")
		self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
		self.logger.handlers.clear()
		self.logger.propagate = False

		fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

		file_handler = logging.FileHandler(run_dir / "pipeline.log", encoding="utf-8")
		file_handler.setFormatter(fmt)
		self.logger.addHandler(file_handler)

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(logging.Formatter("%(message)s"))
		self.logger.addHandler(console_handler)

	def info(self, msg: str) -> None:
		self.logger.info(msg)

	def warning(self, msg: str) -> None:
		self.logger.warning(msg)

	def error(self, msg: str) -> None:
		self.logger.error(msg)


def _now_run_id() -> str:
	return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _prompt_yes_no(prompt: str) -> bool:
	while True:
		ans = input(prompt).strip().lower()
		if ans in {"y", "yes"}:
			return True
		if ans in {"n", "no"}:
			return False
		print("Please enter 'y' or 'n'.")


def _prompt_menu(prompt: str, options: dict[str, str]) -> str:
	"""Prompt for a menu choice.

	options: mapping of choice -> description
	returns the chosen key
	"""
	while True:
		print(prompt)
		for k, desc in options.items():
			print(f"{k}. {desc}")
		choice = input("Select: ").strip()
		if choice in options:
			return choice
		print(f"Invalid choice. Valid options: {', '.join(options.keys())}")


def _list_csv_files_flat(input_dir: Path) -> list[Path]:
	if not input_dir.exists():
		raise FileNotFoundError(
			f"Input directory does not exist: {input_dir}\n"
			"Fix: create it or pass --input_dir <path>."
		)
	if not input_dir.is_dir():
		raise NotADirectoryError(
			f"Input path is not a directory: {input_dir}\n"
			"Fix: pass a directory that contains .csv files."
		)

	return [
		p
		for p in sorted(input_dir.iterdir())
		if p.is_file() and p.suffix.lower() == ".csv"
	]


def _autodetect_timestamp_col(df: pd.DataFrame) -> Optional[str]:
	for c in TIMESTAMP_CANDIDATES:
		if c in df.columns:
			return c
	return None


def _validate_raw_csv(
	csv_path: Path,
	label_col: str,
	timestamp_col: Optional[str],
) -> str:
	"""Validate a raw CSV file and return the timestamp column name to use."""

	try:
		df = pd.read_csv(csv_path)
	except Exception as e:
		raise ValueError(
			f"Failed to read CSV: {csv_path}\n"
			f"Error: {e}\n"
			"Fix: ensure the file is a valid CSV."
		)

	missing_cols = [c for c in ("ax", "ay", "az", label_col) if c not in df.columns]
	if missing_cols:
		raise ValueError(
			f"CSV missing required columns: {csv_path}\n"
			f"Missing: {missing_cols}\n"
			"Fix: ensure your input CSV has accelerometer columns ax/ay/az and a label column.\n"
			f"Label column expected: '{label_col}' (override with --label_col)."
		)

	if len(df) < 5:
		raise ValueError(
			f"CSV has too few rows to process reliably: {csv_path} (rows={len(df)})\n"
			"Fix: record a longer sample or remove this file."
		)

	ts_col = timestamp_col
	if ts_col is None:
		ts_col = _autodetect_timestamp_col(df)
		if ts_col is None:
			raise ValueError(
				f"No timestamp column detected in: {csv_path}\n"
				f"Tried: {list(TIMESTAMP_CANDIDATES)}\n"
				"Fix: rename your timestamp column to one of the above or pass --timestamp_col <col>."
			)

	if ts_col not in df.columns:
		raise ValueError(
			f"Timestamp column '{ts_col}' not found in: {csv_path}\n"
			"Fix: pass the correct --timestamp_col or rename the column."
		)

	# Validate that label_col can be cast to int (matches get_features.process_csv behavior)
	try:
		_ = df[label_col].astype(int)
	except Exception as e:
		raise ValueError(
			f"Label column '{label_col}' cannot be cast to int in: {csv_path}\n"
			f"Error: {e}\n"
			"Fix: ensure labels are 0/1 values (or integers) before running the pipeline."
		)

	return ts_col


def transform_and_archive(
	paths: PipelinePaths,
	runlog: RunLogger,
	postfix: str,
	label_col: str,
	timestamp_col: Optional[str],
	transition_sec: float,
	long_chew_sec: float,
	long_ramp_sec: float,
) -> list[Path]:
	runlog.info("\n=== STEP 1: Transform CSVs (add chewing_soft) ===")

	csv_files = _list_csv_files_flat(paths.input_dir)
	if not csv_files:
		raise FileNotFoundError(
			f"No .csv files found in: {paths.input_dir}\n"
			"Fix: add new raw CSVs there, then rerun."
		)

	paths.csv_output_dir.mkdir(parents=True, exist_ok=True)
	paths.archive_dir.mkdir(parents=True, exist_ok=True)

	transformed_paths: list[Path] = []

	for csv_path in csv_files:
		runlog.info(f"Processing raw CSV: {csv_path.name}")

		ts_col_for_file = _validate_raw_csv(
			csv_path, label_col=label_col, timestamp_col=timestamp_col
		)

		out_name = f"{csv_path.stem}{postfix}{csv_path.suffix}"
		out_path = paths.csv_output_dir / out_name
		if out_path.exists():
			raise FileExistsError(
				f"Transformed output already exists: {out_path}\n"
				"Fix: delete/move the existing transformed file or rename the incoming raw CSV."
			)

		get_features.process_csv(
			input_csv_path=str(csv_path),
			output_csv_path=str(out_path),
			label_col=label_col,
			timestamp_col=ts_col_for_file,
			transition_sec=transition_sec,
			long_chew_sec=long_chew_sec,
			long_ramp_sec=long_ramp_sec,
		)

		dest_path = paths.archive_dir / csv_path.name
		if dest_path.exists():
			raise FileExistsError(
				f"Archive already contains a file named: {dest_path}\n"
				"Fix: move/rename the existing archived file, or rename the new incoming raw CSV."
			)
		shutil.move(str(csv_path), str(dest_path))
		runlog.info(f"Moved original CSV to: {dest_path}")

		transformed_paths.append(out_path)

	runlog.info(
		f"✅ Transform complete. Wrote {len(transformed_paths)} transformed CSV(s) to: {paths.csv_output_dir}"
	)
	return transformed_paths


def generate_features(
	runlog: RunLogger,
	csv_output_dir: Path,
	features_output_dir: Path,
	window_sec: float,
	step_sec: float,
	timestamp_col: Optional[str],
) -> None:
	runlog.info("\n=== STEP 2: Extract features (X.npy / y.npy) ===")
	features_output_dir.mkdir(parents=True, exist_ok=True)

	# This uses your existing, known-working implementation.
	get_features.process_features_directory(
		input_dir=str(csv_output_dir),
		output_dir=str(features_output_dir),
		window_sec=window_sec,
		step_sec=step_sec,
		label_col="chewing_soft",
		timestamp_col=timestamp_col,
	)


def run_stats(
	runlog: RunLogger,
	csv_output_dir: Path,
	timestamp_col: Optional[str],
) -> None:
	runlog.info("\n=== STEP 3: Dataset stats (chewing vs non-chewing) ===")

	chew_sec, non_sec = dataset_stats.compute_stats(
		input_dir=str(csv_output_dir),
		label_col="chewing_soft",
		timestamp_col=timestamp_col,
	)
	dataset_stats.report(chew_sec, non_sec)


def train_model(
	runlog: RunLogger,
	features_output_dir: Path,
	model_path: Path,
	batch_size: int,
	lr: float,
	epochs: int,
	val_ratio: float,
	hidden_dim: int,
	patience: int,
	args: argparse.Namespace,
) -> None:
	runlog.info("\n=== STEP 4: Train model ===")

	x_path = features_output_dir / "X.npy"
	y_path = features_output_dir / "y.npy"
	if not x_path.exists() or not y_path.exists():
		raise FileNotFoundError(
			f"Missing feature files in: {features_output_dir}\n"
			"Expected: X.npy and y.npy\n"
			"Fix: ensure Step 2 completed successfully."
		)

	# Build config dict with all threshold parameters for W&B logging
	config = {
		"transition_sec": args.transition_sec,
		"long_chew_sec": args.long_chew_sec,
		"long_ramp_sec": args.long_ramp_sec,
		"window_sec": args.window_sec,
		"step_sec": args.step_sec,
		"chew_threshold": args.chew_threshold,
		"pred_threshold": args.pred_threshold,
		"alpha": args.alpha,
		"high_threshold": args.high_threshold,
		"low_threshold": args.low_threshold,
		"min_start_windows": args.min_start_windows,
		"min_end_windows": args.min_end_windows,
	}

	train_pytorch.train(
		input_dir=str(features_output_dir),
		output_path=str(model_path),
		batch_size=batch_size,
		lr=lr,
		epochs=epochs,
		val_ratio=val_ratio,
		hidden_dim=hidden_dim,
		patience=patience,
		use_wandb=True,
		wandb_project="chewsense",
		config=config,
	)


def evaluate_model(
	runlog: RunLogger,
	features_output_dir: Path,
	model_path: Path,
	y_threshold: float = 0.5,
	prob_threshold: float = 0.5,
) -> None:
	runlog.info("\n=== STEP 5: Evaluate model ===")

	try:
		from sklearn.metrics import (
			accuracy_score,
			roc_auc_score,
			precision_score,
			recall_score,
			f1_score,
			confusion_matrix,
		)
	except Exception as e:
		raise RuntimeError(
			"scikit-learn is required for evaluation but could not be imported.\n"
			f"Error: {e}\n"
			"Fix: install requirements.txt (pip install -r requirements.txt)."
		)

	ckpt = torch.load(str(model_path), map_location="cpu", weights_only=False)
	mean = ckpt["mean"]
	std = ckpt["std"]

	class ChewNet(torch.nn.Module):
		def __init__(self, input_dim: int, hidden_dim: int = 32):
			super().__init__()
			self.net = torch.nn.Sequential(
				torch.nn.Linear(input_dim, hidden_dim),
				torch.nn.ReLU(),
				torch.nn.Linear(hidden_dim, hidden_dim),
				torch.nn.ReLU(),
				torch.nn.Linear(hidden_dim, 1),
			)

		def forward(self, x: torch.Tensor) -> torch.Tensor:
			return self.net(x).squeeze(-1)

	model = ChewNet(input_dim=ckpt["input_dim"], hidden_dim=ckpt["hidden_dim"])
	model.load_state_dict(ckpt["model_state_dict"])
	model.eval()

	X = np.load(str(features_output_dir / "X.npy")).astype(np.float32)
	y_soft = np.load(str(features_output_dir / "y.npy")).astype(np.float32)

	# IMPORTANT: main.py binarizes y for sklearn classification metrics.
	# TODO: If you want to evaluate against soft targets directly, add regression metrics (MAE/MSE)
	#       or calibration metrics. For now this keeps evaluation stable and interpretable.
	y = (y_soft >= y_threshold).astype(np.int32)

	X = (X - mean) / std
	X_t = torch.from_numpy(X)

	with torch.no_grad():
		logits = model(X_t)
		probs = torch.sigmoid(logits).numpy()

	preds = (probs >= prob_threshold).astype(np.int32)

	acc = accuracy_score(y, preds)
	auc = roc_auc_score(y, probs)
	prec = precision_score(y, preds, zero_division=0)
	rec = recall_score(y, preds, zero_division=0)
	f1 = f1_score(y, preds, zero_division=0)
	cm = confusion_matrix(y, preds)

	runlog.info("\nEVALUATION RESULTS")
	runlog.info("------------------")
	runlog.info(f"Accuracy:   {acc:.4f}")
	runlog.info(f"ROC AUC:    {auc:.4f}")
	runlog.info(f"Precision:  {prec:.4f}")
	runlog.info(f"Recall:     {rec:.4f}")
	runlog.info(f"F1 Score:   {f1:.4f}")
	runlog.info("Confusion Matrix:")
	runlog.info(str(cm))


def _run_subprocess(runlog: RunLogger, args: list[str], cwd: Optional[Path] = None) -> None:
	runlog.info(f"Running: {' '.join(args)}")

	proc = subprocess.run(
		args,
		cwd=str(cwd) if cwd else None,
		capture_output=True,
		text=True,
	)

	if proc.stdout:
		runlog.info(proc.stdout.rstrip())
	if proc.stderr:
		runlog.warning(proc.stderr.rstrip())

	if proc.returncode != 0:
		raise RuntimeError(
			f"Command failed (exit={proc.returncode}): {' '.join(args)}\n"
			"Fix: check logs/pipeline.log for details."
		)


def export_coreml_and_dump_norm(runlog: RunLogger, repo_root: Path) -> None:
	runlog.info("\n=== STEP 6: Export CoreML + dump normalization ===")

	# Keep existing scripts unchanged; they read chewnet.pth from models/ directory.
	_run_subprocess(runlog, [sys.executable, "scripts/export_coreML.py"], cwd=repo_root)
	_run_subprocess(runlog, [sys.executable, "scripts/dump_norm.py"], cwd=repo_root)


def write_run_metadata(
	runlog: RunLogger, run_dir: Path, args: argparse.Namespace, paths: PipelinePaths
) -> None:
	meta = {
		"run_dir": str(run_dir),
		"started_at": _dt.datetime.now().isoformat(),
		"argv": sys.argv,
		"args": vars(args),
		"hyperparameters": {
			"transition_sec": args.transition_sec,
			"long_chew_sec": args.long_chew_sec,
			"long_ramp_sec": args.long_ramp_sec,
			"window_sec": args.window_sec,
			"step_sec": args.step_sec,
			"chew_threshold": args.chew_threshold,
			"pred_threshold": args.pred_threshold,
			"alpha": args.alpha,
			"high_threshold": args.high_threshold,
			"low_threshold": args.low_threshold,
			"min_start_windows": args.min_start_windows,
			"min_end_windows": args.min_end_windows,
			"batch_size": args.batch_size,
			"lr": args.lr,
			"epochs": args.epochs,
			"val_ratio": args.val_ratio,
			"hidden_dim": args.hidden_dim,
			"patience": args.patience,
		},
		"paths": {
			"input_dir": str(paths.input_dir),
			"archive_dir": str(paths.archive_dir),
			"csv_output_dir": str(paths.csv_output_dir),
			"features_output_dir": str(paths.features_output_dir),
			"model_path": str(paths.model_path),
			"logs_root": str(paths.logs_root),
		},
	}

	out = run_dir / "run_config.json"
	out.write_text(json.dumps(meta, indent=2), encoding="utf-8")
	runlog.info(f"Run metadata saved: {out}")


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(
		description="Chew Sense single-command pipeline (transform -> features -> stats -> train/eval/export)",
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	)

	p.add_argument("--input_dir", default="data/raw_sessions", help="Folder containing new raw CSV files")
	p.add_argument(
		"--archive_dir",
		default=None,
		help="Where to move processed raw CSVs (default: data/raw_sessions/processed)",
	)

	p.add_argument("--csv_output_dir", default="data/transformed", help="Folder for transformed CSVs")
	p.add_argument("--features_output_dir", default="data/features", help="Folder for X.npy/y.npy outputs")

	p.add_argument("--model_path", default="models/chewnet.pth", help="Output checkpoint path")

	p.add_argument("--postfix", default="_transformed", help="Postfix added to transformed CSV filenames")

	p.add_argument("--label_col", default="label", help="Raw label column (0/1) in input CSVs")
	p.add_argument("--timestamp_col", default=None, help="Timestamp column name (auto-detect if omitted)")

	p.add_argument("--transition_sec", type=float, default=0.6, help="Short chew transition window")
	p.add_argument("--long_chew_sec", type=float, default=3.0, help="Threshold for long chew detection")
	p.add_argument("--long_ramp_sec", type=float, default=1.5, help="Ramp time for long chews")

	p.add_argument("--window_sec", type=float, default=0.75, help="Feature extraction window size")
	p.add_argument("--step_sec", type=float, default=0.1, help="Sliding window step size")

	# Threshold parameters for evaluation and runtime detection
	p.add_argument("--chew_threshold", type=float, default=0.5, help="Threshold for binarizing soft labels during evaluation")
	p.add_argument("--pred_threshold", type=float, default=0.5, help="Threshold for converting model probabilities to binary predictions")
	
	# State machine parameters for real-time detection
	p.add_argument("--alpha", type=float, default=0.4, help="EMA smoothing factor for real-time detection")
	p.add_argument("--high_threshold", type=float, default=0.6, help="Probability threshold to start chewing episode")
	p.add_argument("--low_threshold", type=float, default=0.4, help="Probability threshold to end chewing episode")
	p.add_argument("--min_start_windows", type=int, default=3, help="Consecutive windows required to trigger chewing start")
	p.add_argument("--min_end_windows", type=int, default=2, help="Consecutive windows required to trigger chewing end")

	p.add_argument("--stats", action="store_true", help="Print dataset stats after feature generation")

	p.add_argument("--batch_size", type=int, default=256)
	p.add_argument("--lr", type=float, default=1e-3)
	p.add_argument("--epochs", type=int, default=50)
	p.add_argument("--val_ratio", type=float, default=0.2)
	p.add_argument("--hidden_dim", type=int, default=32)
	p.add_argument("--patience", type=int, default=5)

	p.add_argument("--log_level", default="INFO", help="Logging level (INFO/DEBUG/WARNING)")

	return p


def main() -> None:
	args = build_parser().parse_args()

	repo_root = Path(__file__).resolve().parent

	input_dir = (repo_root / args.input_dir).resolve()
	csv_output_dir = (repo_root / args.csv_output_dir).resolve()
	features_output_dir = (repo_root / args.features_output_dir).resolve()
	model_path = (repo_root / args.model_path).resolve()

	if args.archive_dir is None:
		archive_dir = input_dir / "processed"
	else:
		archive_dir = (repo_root / args.archive_dir).resolve()

	logs_root = (repo_root / "logs").resolve()
	run_dir = logs_root / "runs" / _now_run_id()

	runlog = RunLogger(run_dir=run_dir, log_level=args.log_level)

	paths = PipelinePaths(
		input_dir=input_dir,
		archive_dir=archive_dir,
		csv_output_dir=csv_output_dir,
		features_output_dir=features_output_dir,
		model_path=model_path,
		logs_root=logs_root,
	)

	write_run_metadata(runlog, run_dir, args, paths)

	runlog.info("\nChew Sense Pipeline")
	runlog.info("------------------")
	runlog.info(f"Input dir:      {paths.input_dir}")
	runlog.info(f"Archive dir:    {paths.archive_dir}")
	runlog.info(f"Transformed:    {paths.csv_output_dir}")
	runlog.info(f"Features:       {paths.features_output_dir}")
	runlog.info(f"Model path:     {paths.model_path}")
	runlog.info(f"Logs run dir:   {run_dir}")

	transform_and_archive(
		paths=paths,
		runlog=runlog,
		postfix=args.postfix,
		label_col=args.label_col,
		timestamp_col=args.timestamp_col,
		transition_sec=args.transition_sec,
		long_chew_sec=args.long_chew_sec,
		long_ramp_sec=args.long_ramp_sec,
	)

	generate_features(
		runlog=runlog,
		csv_output_dir=paths.csv_output_dir,
		features_output_dir=paths.features_output_dir,
		window_sec=args.window_sec,
		step_sec=args.step_sec,
		timestamp_col=args.timestamp_col,
	)

	if args.stats:
		run_stats(
			runlog=runlog,
			csv_output_dir=paths.csv_output_dir,
			timestamp_col=args.timestamp_col,
		)

	if _prompt_yes_no("\nTrain model? (y/n): "):
		train_model(
			runlog=runlog,
			features_output_dir=paths.features_output_dir,
			model_path=paths.model_path,
			batch_size=args.batch_size,
			lr=args.lr,
			epochs=args.epochs,
			val_ratio=args.val_ratio,
			hidden_dim=args.hidden_dim,
			patience=args.patience,
			args=args,
		)

		choice = _prompt_menu(
			"\nNext step:",
			{
				"1": "evaluate model",
				"2": "export ML and dump norm",
			},
		)

		if choice == "1":
			evaluate_model(
				runlog=runlog,
				features_output_dir=paths.features_output_dir,
				model_path=paths.model_path,
				y_threshold=args.chew_threshold,
				prob_threshold=args.pred_threshold,
			)

			if _prompt_yes_no("\nExport ML and dump norm? (y/n): "):
				export_coreml_and_dump_norm(runlog=runlog, repo_root=repo_root)

		elif choice == "2":
			export_coreml_and_dump_norm(runlog=runlog, repo_root=repo_root)

	else:
		runlog.info("\nSkipped training.")

	runlog.info("\n✅ Pipeline complete.")


if __name__ == "__main__":
	main()
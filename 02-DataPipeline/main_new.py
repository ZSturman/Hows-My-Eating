#!/usr/bin/env python3
"""
ChewSense Pipeline CLI

A modular, composable pipeline for chewing detection model development.

Usage:
    python main.py sample          # Run with sample data (demo/testing)
    python main.py from-app        # Guide for collecting your own data
    python main.py from-raw        # Process raw labeled CSVs
    python main.py from-features   # Train from pre-extracted features
    python main.py deploy          # Deploy model to Xcode project

Each command supports --help for detailed options.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure pipeline module is importable
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.config import load_config, merge_cli_args, PipelineConfig
from pipeline.ingest import validate_sessions, create_manifest, save_manifest
from pipeline.transform import transform_directory
from pipeline.features import extract_features_directory
from pipeline.train import train_model
from pipeline.evaluate import evaluate_model
from pipeline.export import export_coreml, export_normalization_json, generate_swift_constants
from pipeline.deploy import deploy_to_app


def get_repo_root() -> Path:
    """Get repository root (parent of 02-DataPipeline)."""
    return Path(__file__).parent.parent


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments to a parser."""
    parser.add_argument(
        "--config", type=Path, default=None,
        help="Path to config YAML file (default: config/defaults.yaml)"
    )
    parser.add_argument(
        "--no-wandb", action="store_true",
        help="Disable Weights & Biases logging"
    )
    
    # Training overrides
    parser.add_argument("--batch-size", type=int, help="Training batch size")
    parser.add_argument("--lr", type=float, help="Learning rate")
    parser.add_argument("--epochs", type=int, help="Max training epochs")
    parser.add_argument("--hidden-dim", type=int, help="Hidden layer dimension")
    parser.add_argument("--patience", type=int, help="Early stopping patience")
    
    # Feature overrides
    parser.add_argument("--window-sec", type=float, help="Feature window duration")
    parser.add_argument("--step-sec", type=float, help="Feature window step")
    
    # Runtime overrides (logged with model)
    parser.add_argument("--alpha", type=float, help="EMA smoothing factor")
    parser.add_argument("--high-threshold", type=float, help="Chewing start threshold")
    parser.add_argument("--low-threshold", type=float, help="Chewing end threshold")


def load_and_merge_config(args: argparse.Namespace) -> PipelineConfig:
    """Load config and merge CLI overrides."""
    config = load_config(args.config)
    
    if args.no_wandb:
        config.wandb.enabled = False
    
    # Convert args to dict with underscores
    args_dict = {
        "batch_size": getattr(args, "batch_size", None),
        "lr": args.lr if hasattr(args, "lr") else None,
        "epochs": args.epochs if hasattr(args, "epochs") else None,
        "hidden_dim": getattr(args, "hidden_dim", None),
        "patience": args.patience if hasattr(args, "patience") else None,
        "window_sec": getattr(args, "window_sec", None),
        "step_sec": getattr(args, "step_sec", None),
        "alpha": args.alpha if hasattr(args, "alpha") else None,
        "high_threshold": getattr(args, "high_threshold", None),
        "low_threshold": getattr(args, "low_threshold", None),
    }
    
    return merge_cli_args(config, args_dict)


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt user for yes/no confirmation."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        ans = input(prompt + suffix).strip().lower()
        if ans == "":
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


# =============================================================================
# COMMAND: sample
# =============================================================================

def cmd_sample(args: argparse.Namespace) -> int:
    """Run pipeline with sample data (for testing/demo)."""
    print("\n🧪 Running pipeline with SAMPLE data")
    print("=" * 50)
    
    config = load_and_merge_config(args)
    repo_root = get_repo_root()
    pipeline_root = Path(__file__).parent
    
    # Paths for sample workflow
    sample_dir = pipeline_root / "data" / "sample"
    derived_dir = pipeline_root / "data" / "derived"
    transformed_dir = derived_dir / "transformed"
    features_dir = derived_dir / "features"
    model_path = pipeline_root / "models" / "chewnet.pth"
    
    # Check sample data exists
    if not sample_dir.exists() or not list(sample_dir.glob("*/*.csv")):
        print(f"\n❌ No sample data found in: {sample_dir}")
        print("   Sample data should be pre-populated in the repository.")
        return 1
    
    # 1. Validate
    print("\n📋 Step 1: Validating sample data...")
    sessions = validate_sessions(sample_dir)
    manifest = create_manifest(sessions)
    print(f"   Found {len(sessions)} sessions")
    print(f"   Dataset hash: {manifest.dataset_hash}")
    
    # 2. Transform
    print("\n🔄 Step 2: Transforming (adding soft labels)...")
    transform_directory(
        input_dir=sample_dir,
        output_dir=transformed_dir,
        config=config.soft_labels,
        postfix="_transformed",
    )
    
    # 3. Extract features
    print("\n📊 Step 3: Extracting features...")
    extract_features_directory(
        input_dir=transformed_dir,
        output_dir=features_dir,
        config=config.features,
    )
    
    # 4. Train
    if prompt_yes_no("\n🎯 Train model?"):
        result = train_model(
            features_dir=features_dir,
            output_path=model_path,
            config=config,
            dataset_hash=manifest.dataset_hash,
            data_source="sample",
        )
        
        # 5. Evaluate
        if prompt_yes_no("\n📈 Evaluate model?"):
            evaluate_model(features_dir, model_path, config)
        
        # 6. Export
        if prompt_yes_no("\n📦 Export to CoreML?"):
            exports_dir = pipeline_root / "exports"
            export_coreml(model_path, exports_dir / "ChewNet.mlpackage")
            export_normalization_json(model_path, exports_dir / "chewnet_norm.json")
            generate_swift_constants(
                model_path,
                exports_dir / "NormalizationConstants.swift",
            )
    
    print("\n✅ Sample pipeline complete!")
    return 0


# =============================================================================
# COMMAND: from-app
# =============================================================================

def cmd_from_app(args: argparse.Namespace) -> int:
    """Guide user through collecting and processing their own data."""
    print("\n📱 Collecting Your Own Data")
    print("=" * 50)
    
    print("""
This workflow guides you through:
1. Recording sessions with the ChewSense Data Collection app
2. Exporting and placing data in the correct location
3. Running the training pipeline

STEP 1: Install the App
-----------------------
Download from the App Store:
https://apps.apple.com/us/app/chew-sense-collect-and-label/id6755277802

STEP 2: Required Hardware
-------------------------
You MUST use AirPods with motion sensors:
  ✅ AirPods Pro (1st or 2nd generation)
  ✅ AirPods Max
  ✅ AirPods 4 (with Active Noise Cancellation)
  ❌ AirPods 3 (no motion sensors)
  ❌ AirPods 2 or earlier

STEP 3: Record Sessions
-----------------------
Record a mix of eating and not-eating sessions:
  • Aim for at least 5-10 minutes of each
  • Label sessions accurately during recording
  • Include variety: different foods, activities, head movements

STEP 4: Export Sessions
-----------------------
Use the app's export feature to share session folders.
Each session folder contains:
  • <SessionName>.csv    (motion data + labels)
  • <SessionName>.mov    (video, optional)
  • _metadata.txt

STEP 5: Place Data
------------------
Copy exported session folders to:
""")
    
    pipeline_root = Path(__file__).parent
    user_data_dir = pipeline_root / "data" / "user" / "raw_sessions"
    print(f"  {user_data_dir}")
    
    print(f"""
STEP 6: Run Pipeline
--------------------
Once data is in place, run:

    python main.py from-raw --input data/user/raw_sessions

This will validate, transform, extract features, and train a model.
""")
    
    if prompt_yes_no("Have you placed data in the user directory?", default=False):
        print("\nGreat! Running from-raw workflow...")
        args.input = user_data_dir
        return cmd_from_raw(args)
    else:
        print("\nOK! Come back when you have data ready.")
        return 0


# =============================================================================
# COMMAND: from-raw
# =============================================================================

def cmd_from_raw(args: argparse.Namespace) -> int:
    """Process raw labeled CSVs through full pipeline."""
    print("\n📁 Processing Raw Labeled Data")
    print("=" * 50)
    
    config = load_and_merge_config(args)
    pipeline_root = Path(__file__).parent
    
    input_dir = Path(args.input) if args.input else pipeline_root / "data" / "user" / "raw_sessions"
    
    if not input_dir.exists():
        print(f"\n❌ Input directory not found: {input_dir}")
        return 1
    
    derived_dir = pipeline_root / "data" / "derived"
    transformed_dir = derived_dir / "transformed"
    features_dir = derived_dir / "features"
    model_path = pipeline_root / "models" / "chewnet.pth"
    
    # 1. Validate
    print(f"\n📋 Step 1: Validating data in {input_dir}...")
    try:
        sessions = validate_sessions(input_dir)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1
    
    manifest = create_manifest(sessions)
    print(f"   Found {len(sessions)} sessions:")
    print(f"   - Eating: {manifest.eating_count}")
    print(f"   - Not-eating: {manifest.not_eating_count}")
    print(f"   - Total duration: {manifest.total_duration_sec:.1f}s")
    print(f"   - Dataset hash: {manifest.dataset_hash}")
    
    # Save manifest
    manifest_path = derived_dir / "logs" / "dataset_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    save_manifest(manifest, manifest_path)
    
    # 2. Transform
    print("\n🔄 Step 2: Transforming (adding soft labels)...")
    transform_directory(
        input_dir=input_dir,
        output_dir=transformed_dir,
        config=config.soft_labels,
        archive_dir=derived_dir / "archived_raw",
    )
    
    # 3. Extract features
    print("\n📊 Step 3: Extracting features...")
    extract_features_directory(
        input_dir=transformed_dir,
        output_dir=features_dir,
        config=config.features,
    )
    
    # 4. Train
    if prompt_yes_no("\n🎯 Train model?"):
        result = train_model(
            features_dir=features_dir,
            output_path=model_path,
            config=config,
            dataset_hash=manifest.dataset_hash,
            data_source="user",
        )
        
        if prompt_yes_no("\n📈 Evaluate model?"):
            evaluate_model(features_dir, model_path, config)
        
        if prompt_yes_no("\n📦 Export and deploy to Xcode?"):
            deploy_to_app(
                model_path=model_path,
                repo_root=get_repo_root(),
            )
    
    print("\n✅ Pipeline complete!")
    return 0


# =============================================================================
# COMMAND: from-features
# =============================================================================

def cmd_from_features(args: argparse.Namespace) -> int:
    """Train from pre-extracted features (skip transform/extraction)."""
    print("\n📊 Training from Pre-Extracted Features")
    print("=" * 50)
    
    config = load_and_merge_config(args)
    pipeline_root = Path(__file__).parent
    
    features_dir = Path(args.input) if args.input else pipeline_root / "data" / "derived" / "features"
    model_path = pipeline_root / "models" / "chewnet.pth"
    
    # Check features exist
    x_path = features_dir / "X.npy"
    y_path = features_dir / "y.npy"
    
    if not x_path.exists() or not y_path.exists():
        print(f"\n❌ Feature files not found in: {features_dir}")
        print("   Expected: X.npy and y.npy")
        print("\n   Run 'python main.py from-raw' to extract features first.")
        return 1
    
    print(f"\n📂 Features directory: {features_dir}")
    
    # Train
    result = train_model(
        features_dir=features_dir,
        output_path=model_path,
        config=config,
        data_source="user",
    )
    
    if prompt_yes_no("\n📈 Evaluate model?"):
        evaluate_model(features_dir, model_path, config)
    
    if prompt_yes_no("\n📦 Export and deploy to Xcode?"):
        deploy_to_app(
            model_path=model_path,
            repo_root=get_repo_root(),
        )
    
    print("\n✅ Training complete!")
    return 0


# =============================================================================
# COMMAND: deploy
# =============================================================================

def cmd_deploy(args: argparse.Namespace) -> int:
    """Deploy trained model to Xcode project."""
    print("\n🚀 Deploying Model to Xcode Project")
    print("=" * 50)
    
    pipeline_root = Path(__file__).parent
    model_path = Path(args.model) if args.model else pipeline_root / "models" / "chewnet.pth"
    
    if not model_path.exists():
        print(f"\n❌ Model not found: {model_path}")
        print("   Train a model first with 'python main.py sample' or 'python main.py from-raw'")
        return 1
    
    deploy_to_app(
        model_path=model_path,
        repo_root=get_repo_root(),
        force=args.force,
    )
    
    return 0


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ChewSense Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py sample              # Quick demo with sample data
  python main.py from-app            # Collect your own data
  python main.py from-raw --input data/user/raw_sessions
  python main.py deploy --force      # Deploy model to Xcode
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # sample command
    p_sample = subparsers.add_parser(
        "sample",
        help="Run pipeline with sample data (for demo/testing)",
    )
    add_common_args(p_sample)
    p_sample.set_defaults(func=cmd_sample)
    
    # from-app command
    p_from_app = subparsers.add_parser(
        "from-app",
        help="Guide for collecting and processing your own data",
    )
    add_common_args(p_from_app)
    p_from_app.set_defaults(func=cmd_from_app)
    
    # from-raw command
    p_from_raw = subparsers.add_parser(
        "from-raw",
        help="Process raw labeled CSVs through full pipeline",
    )
    p_from_raw.add_argument(
        "--input", type=Path,
        help="Directory containing raw session folders or CSVs",
    )
    add_common_args(p_from_raw)
    p_from_raw.set_defaults(func=cmd_from_raw)
    
    # from-features command
    p_from_features = subparsers.add_parser(
        "from-features",
        help="Train from pre-extracted features (skip transform/extraction)",
    )
    p_from_features.add_argument(
        "--input", type=Path,
        help="Directory containing X.npy and y.npy",
    )
    add_common_args(p_from_features)
    p_from_features.set_defaults(func=cmd_from_features)
    
    # deploy command
    p_deploy = subparsers.add_parser(
        "deploy",
        help="Deploy trained model to Xcode project",
    )
    p_deploy.add_argument(
        "--model", type=Path,
        help="Path to trained model checkpoint",
    )
    p_deploy.add_argument(
        "--force", action="store_true",
        help="Overwrite existing files",
    )
    p_deploy.set_defaults(func=cmd_deploy)
    
    # Parse and run
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        print("\n💡 Quick start: python main.py sample")
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

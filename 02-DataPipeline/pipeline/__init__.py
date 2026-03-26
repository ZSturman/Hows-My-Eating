"""
ChewSense Pipeline Module

This module provides a modular, composable pipeline for chewing detection:

Stages:
1. ingest    - Validate raw CSVs, compute dataset manifest
2. transform - Add soft labels (chewing_soft column)
3. features  - Extract 12-feature vectors from transformed CSVs
4. train     - Train ChewNet model with W&B logging
5. evaluate  - Compute classification metrics
6. export    - Export to CoreML + generate Swift constants
7. deploy    - Copy artifacts to Xcode project

Usage:
    from pipeline import ingest, transform, features, train, evaluate, export, deploy
"""

from .config import load_config, PipelineConfig
from .ingest import validate_sessions, compute_dataset_hash
from .transform import transform_csv, transform_directory
from .features import extract_features, extract_features_directory
from .train import train_model
from .evaluate import evaluate_model
from .export import export_coreml, generate_swift_constants
from .deploy import deploy_to_app
from .mouth_shape import extract_mouth_shape_from_video, extract_and_save
from .align import align_mouth_shape_to_motion, align_directory, process_videos_and_align

__all__ = [
    # Config
    "load_config",
    "PipelineConfig",
    # Stages
    "validate_sessions",
    "compute_dataset_hash",
    "transform_csv",
    "transform_directory",
    "extract_features",
    "extract_features_directory",
    "train_model",
    "evaluate_model",
    "export_coreml",
    "generate_swift_constants",
    "deploy_to_app",
    # Mouth shape
    "extract_mouth_shape_from_video",
    "extract_and_save",
    "align_mouth_shape_to_motion",
    "align_directory",
    "process_videos_and_align",
]

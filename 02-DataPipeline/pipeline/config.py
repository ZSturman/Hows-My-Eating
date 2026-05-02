"""
Pipeline configuration management.

Loads defaults from config/defaults.yaml and allows CLI/programmatic overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import yaml


@dataclass
class AugmentationConfig:
    """Per-axis raw-window augmentation (only used when input_mode includes raw)."""
    enabled: bool = False
    noise_std: float = 0.01      # Gaussian noise std (in g / rad/s)
    rotation_deg: float = 8.0    # max random rotation around random axis
    time_shift_frac: float = 0.05  # max fraction of window to shift
    channel_dropout_p: float = 0.0  # probability of zeroing one channel


@dataclass
class TrainingConfig:
    batch_size: int = 256
    lr: float = 0.001
    epochs: int = 50
    val_ratio: float = 0.2
    hidden_dim: int = 32
    patience: int = 5
    # Imbalance handling
    loss: str = "bce"            # "bce" | "focal"
    pos_weight: str = "auto"     # "auto" (n_neg/n_pos), "none", or float string e.g. "2.5"
    use_weighted_sampler: bool = True
    focal_alpha: float = 0.25
    focal_gamma: float = 2.0
    # Architecture
    arch: str = "mlp"            # "mlp" | "cnn"
    # Split policy
    allow_unsplit: bool = False  # If True, fall back to session-aware random split
    # Feature-level augmentation (cheap noise on the 12-dim vector)
    feature_noise_std: float = 0.0
    # Raw-window augmentation (only if features include raw windows; future phase)
    augmentation: AugmentationConfig = field(default_factory=AugmentationConfig)


@dataclass
class FeaturesConfig:
    window_sec: float = 0.75
    step_sec: float = 0.10


@dataclass
class SoftLabelsConfig:
    transition_sec: float = 0.6
    long_chew_sec: float = 3.0
    long_ramp_sec: float = 1.5


@dataclass
class EvaluationConfig:
    chew_threshold: float = 0.5
    pred_threshold: float = 0.5


@dataclass
class RuntimeConfig:
    """Runtime inference parameters for the iOS/macOS app."""
    alpha: float = 0.4
    high_threshold: float = 0.6
    low_threshold: float = 0.4
    min_start_windows: int = 3
    min_end_windows: int = 2


@dataclass
class MouthShapeConfig:
    """Configuration for mouth shape regression mode."""
    enabled: bool = False
    parameters: list[str] = field(default_factory=lambda: [
        "mouth_openness", "mouth_width", "jaw_displacement", "lip_compression"
    ])
    num_outputs: int = 4
    video_fps: float = 30.0
    interpolation: str = "linear"
    temporal_smooth_sigma: float = 0.0


@dataclass
class WandbConfig:
    project: str = "chewsense"
    entity: Optional[str] = None
    enabled: bool = True


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    training: TrainingConfig = field(default_factory=TrainingConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    soft_labels: SoftLabelsConfig = field(default_factory=SoftLabelsConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    mouth_shape: MouthShapeConfig = field(default_factory=MouthShapeConfig)
    wandb: WandbConfig = field(default_factory=WandbConfig)
    
    # Paths (set at runtime)
    input_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    model_path: Optional[Path] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for W&B logging."""
        return {
            "training": {
                "batch_size": self.training.batch_size,
                "lr": self.training.lr,
                "epochs": self.training.epochs,
                "val_ratio": self.training.val_ratio,
                "hidden_dim": self.training.hidden_dim,
                "patience": self.training.patience,
                "loss": self.training.loss,
                "pos_weight": self.training.pos_weight,
                "use_weighted_sampler": self.training.use_weighted_sampler,
                "focal_alpha": self.training.focal_alpha,
                "focal_gamma": self.training.focal_gamma,
                "arch": self.training.arch,
                "allow_unsplit": self.training.allow_unsplit,
                "feature_noise_std": self.training.feature_noise_std,
                "augmentation": {
                    "enabled": self.training.augmentation.enabled,
                    "noise_std": self.training.augmentation.noise_std,
                    "rotation_deg": self.training.augmentation.rotation_deg,
                    "time_shift_frac": self.training.augmentation.time_shift_frac,
                    "channel_dropout_p": self.training.augmentation.channel_dropout_p,
                },
            },
            "features": {
                "window_sec": self.features.window_sec,
                "step_sec": self.features.step_sec,
            },
            "soft_labels": {
                "transition_sec": self.soft_labels.transition_sec,
                "long_chew_sec": self.soft_labels.long_chew_sec,
                "long_ramp_sec": self.soft_labels.long_ramp_sec,
            },
            "evaluation": {
                "chew_threshold": self.evaluation.chew_threshold,
                "pred_threshold": self.evaluation.pred_threshold,
            },
            "runtime": {
                "alpha": self.runtime.alpha,
                "high_threshold": self.runtime.high_threshold,
                "low_threshold": self.runtime.low_threshold,
                "min_start_windows": self.runtime.min_start_windows,
                "min_end_windows": self.runtime.min_end_windows,
            },
            "mouth_shape": {
                "enabled": self.mouth_shape.enabled,
                "parameters": self.mouth_shape.parameters,
                "num_outputs": self.mouth_shape.num_outputs,
                "video_fps": self.mouth_shape.video_fps,
                "interpolation": self.mouth_shape.interpolation,
                "temporal_smooth_sigma": self.mouth_shape.temporal_smooth_sigma,
            },
        }


def load_config(config_path: Optional[Path] = None) -> PipelineConfig:
    """
    Load pipeline configuration.
    
    Args:
        config_path: Path to YAML config file. If None, loads defaults.yaml
                     from the config/ directory.
    
    Returns:
        PipelineConfig with all parameters loaded.
    """
    if config_path is None:
        # Find defaults.yaml relative to this file
        pipeline_dir = Path(__file__).parent
        config_path = pipeline_dir.parent / "config" / "defaults.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        # Return defaults if no config file
        return PipelineConfig()
    
    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}
    
    # Build config from YAML
    training = TrainingConfig(**{k: v for k, v in data.get("training", {}).items() if k != "augmentation"})
    aug_data = data.get("training", {}).get("augmentation", {})
    if aug_data:
        training.augmentation = AugmentationConfig(**aug_data)
    features = FeaturesConfig(**data.get("features", {}))
    soft_labels = SoftLabelsConfig(**data.get("soft_labels", {}))
    evaluation = EvaluationConfig(**data.get("evaluation", {}))
    runtime = RuntimeConfig(**data.get("runtime", {}))
    wandb = WandbConfig(**data.get("wandb", {}))

    ms_data = data.get("mouth_shape", {})
    default_mouth_params = [
        "mouth_openness",
        "mouth_width",
        "jaw_displacement",
        "lip_compression",
    ]
    mouth_shape = MouthShapeConfig(
        enabled=ms_data.get("enabled", False),
        parameters=ms_data.get("parameters", default_mouth_params),
        num_outputs=ms_data.get("num_outputs", 4),
        video_fps=ms_data.get("video_fps", 30.0),
        interpolation=ms_data.get("interpolation", "linear"),
        temporal_smooth_sigma=ms_data.get("temporal_smooth_sigma", 0.0),
    )

    return PipelineConfig(
        training=training,
        features=features,
        soft_labels=soft_labels,
        evaluation=evaluation,
        runtime=runtime,
        mouth_shape=mouth_shape,
        wandb=wandb,
    )


def merge_cli_args(config: PipelineConfig, args: dict[str, Any]) -> PipelineConfig:
    """
    Merge CLI arguments into config, overriding YAML values.
    
    Args:
        config: Base configuration
        args: Dictionary of CLI arguments (from argparse.Namespace)
    
    Returns:
        Updated PipelineConfig
    """
    # Training overrides
    if "batch_size" in args and args["batch_size"] is not None:
        config.training.batch_size = args["batch_size"]
    if "lr" in args and args["lr"] is not None:
        config.training.lr = args["lr"]
    if "epochs" in args and args["epochs"] is not None:
        config.training.epochs = args["epochs"]
    if "val_ratio" in args and args["val_ratio"] is not None:
        config.training.val_ratio = args["val_ratio"]
    if "hidden_dim" in args and args["hidden_dim"] is not None:
        config.training.hidden_dim = args["hidden_dim"]
    if "patience" in args and args["patience"] is not None:
        config.training.patience = args["patience"]
    if "loss" in args and args["loss"] is not None:
        config.training.loss = args["loss"]
    if "pos_weight" in args and args["pos_weight"] is not None:
        config.training.pos_weight = str(args["pos_weight"])
    if "use_weighted_sampler" in args and args["use_weighted_sampler"] is not None:
        config.training.use_weighted_sampler = bool(args["use_weighted_sampler"])
    if "arch" in args and args["arch"] is not None:
        config.training.arch = args["arch"]
    if "allow_unsplit" in args and args["allow_unsplit"] is not None:
        config.training.allow_unsplit = bool(args["allow_unsplit"])
    if "feature_noise_std" in args and args["feature_noise_std"] is not None:
        config.training.feature_noise_std = float(args["feature_noise_std"])
    
    # Feature overrides
    if "window_sec" in args and args["window_sec"] is not None:
        config.features.window_sec = args["window_sec"]
    if "step_sec" in args and args["step_sec"] is not None:
        config.features.step_sec = args["step_sec"]
    
    # Soft label overrides
    if "transition_sec" in args and args["transition_sec"] is not None:
        config.soft_labels.transition_sec = args["transition_sec"]
    if "long_chew_sec" in args and args["long_chew_sec"] is not None:
        config.soft_labels.long_chew_sec = args["long_chew_sec"]
    if "long_ramp_sec" in args and args["long_ramp_sec"] is not None:
        config.soft_labels.long_ramp_sec = args["long_ramp_sec"]
    
    # Runtime overrides
    if "alpha" in args and args["alpha"] is not None:
        config.runtime.alpha = args["alpha"]
    if "high_threshold" in args and args["high_threshold"] is not None:
        config.runtime.high_threshold = args["high_threshold"]
    if "low_threshold" in args and args["low_threshold"] is not None:
        config.runtime.low_threshold = args["low_threshold"]
    if "min_start_windows" in args and args["min_start_windows"] is not None:
        config.runtime.min_start_windows = args["min_start_windows"]
    if "min_end_windows" in args and args["min_end_windows"] is not None:
        config.runtime.min_end_windows = args["min_end_windows"]
    
    return config

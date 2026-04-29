"""ChewSense pipeline module.

The package initializer intentionally avoids importing CoreML/export helpers.
Those imports can be slow or environment-sensitive, and basic commands like
``main_new.py --help`` should not require CoreML tooling.
"""

from .config import PipelineConfig, load_config

__all__ = [
    # Config
    "load_config",
    "PipelineConfig",
]

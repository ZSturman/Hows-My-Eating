import json
import torch

"""
dump_norm.py

Utility script to extract the feature normalization statistics (mean and std)
from a trained ChewNet checkpoint (chewnet.pth) and write them to a JSON file.

Usage:
    python3 dump_norm.py --checkpoint chewnet.pth --output chewnet_norm.json

The output JSON will look like:

{
  "input_dim": 12,
  "mean": [m0, m1, ..., m11],
  "std":  [s0, s1, ..., s11]
}

You can then paste these arrays into your Swift code (FEATURE_MEAN and FEATURE_STD)
to perform the same normalization on-device as during training.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Dump normalization stats (mean/std) from chewnet.pth")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="chewnet.pth",
        help="Path to the trained checkpoint (default: chewnet.pth)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="chewnet_norm.json",
        help="Output JSON file for mean/std (default: chewnet_norm.json)",
    )
    args = parser.parse_args()

    # Explicitly set weights_only=False so we can load the full checkpoint dict,
    # including non-tensor entries like mean/std saved from training.
    # This is safe here because the checkpoint is your own file.
    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)

    if "mean" not in ckpt or "std" not in ckpt:
        raise KeyError(
            "Checkpoint does not contain 'mean' and 'std'. "
            "Make sure you saved them in train_pytorch.py."
        )

    mean = ckpt["mean"]
    std = ckpt["std"]

    # Convert to plain Python lists
    if hasattr(mean, "tolist"):
        mean_list = mean.tolist()
    else:
        mean_list = list(mean)

    if hasattr(std, "tolist"):
        std_list = std.tolist()
    else:
        std_list = list(std)

    input_dim = ckpt.get("input_dim", len(mean_list))

    data = {
        "input_dim": input_dim,
        "mean": mean_list,
        "std": std_list,
    }

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote normalization stats to {args.output}")
    print(f"input_dim = {input_dim}")
    print("mean =", mean_list)
    print("std  =", std_list)


if __name__ == "__main__":
    main()

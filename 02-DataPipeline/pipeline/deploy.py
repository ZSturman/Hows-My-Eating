"""
Deploy stage: Copy artifacts to Xcode project.

This stage copies the trained model and generated constants to the
iOS/macOS testing app, ensuring all references are up to date.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .export import (
    compute_mlpackage_sha256,
    export_coreml,
    export_normalization_json,
    generate_swift_constants,
)


# Default paths relative to repository root
DEFAULT_EXPORTS_DIR = "exports"
DEFAULT_XCODE_PROJECT = "04-RealWorldTesting/ChewSense-RealTime/ChewSenseDebuggingModel"
DEFAULT_GENERATED_DIR = "Generated"

# Versions of torch known to crash inside coremltools.convert on macOS arm64.
# Update as compatibility improves.
_LAST_TESTED_TORCH = (2, 7)


def _check_export_env() -> dict:
    """Print resolved versions of the export toolchain and warn on known bad combos.

    Returns a dict with the resolved versions for logging. Does not exit; the
    caller decides whether to proceed.
    """
    info = {"python": sys.version.split()[0]}
    try:
        import torch  # type: ignore
        info["torch"] = torch.__version__
    except Exception as exc:  # pragma: no cover - torch is required elsewhere
        info["torch"] = f"missing ({exc})"
    try:
        import coremltools as ct  # type: ignore
        info["coremltools"] = ct.__version__
    except Exception as exc:
        info["coremltools"] = f"missing ({exc})"
    try:
        import numpy as np  # type: ignore
        info["numpy"] = np.__version__
    except Exception as exc:
        info["numpy"] = f"missing ({exc})"

    print("\n🔧 Export environment:")
    for key in ("python", "torch", "coremltools", "numpy"):
        print(f"   {key:<12} {info.get(key, 'unknown')}")

    torch_ver = info.get("torch", "")
    m = re.match(r"(\d+)\.(\d+)", str(torch_ver))
    if m:
        major, minor = int(m.group(1)), int(m.group(2))
        if (major, minor) > _LAST_TESTED_TORCH:
            print(
                "   ⚠️  torch "
                f"{torch_ver} is newer than the last version tested with coremltools"
                f" ({'.'.join(str(x) for x in _LAST_TESTED_TORCH)}.x). CoreML conversion\n"
                "      may segfault. If you hit a crash, create an export-only venv:\n"
                "        python3 -m venv .venv-export && source .venv-export/bin/activate\n"
                "        pip install 'torch==2.7.*' 'coremltools>=8.1,<10' numpy\n"
                "      and re-run the deploy command from there."
            )
    return info


def _read_swift_constant(swift_path: Path, name: str) -> str:
    """Best-effort scrape of a `static let NAME: ... = "value"` constant."""
    if not swift_path.exists():
        return ""
    try:
        text = swift_path.read_text()
    except OSError:
        return ""
    match = re.search(
        rf'static\s+let\s+{re.escape(name)}\s*:\s*\w+\s*=\s*"([^"]*)"',
        text,
    )
    return match.group(1) if match else ""


def _short(value: str, length: int = 12) -> str:
    return (value[:length] + "…") if value and len(value) > length else (value or "")


def _print_diff_table(before: dict, after: dict) -> None:
    keys = [
        "MODEL_ID",
        "DATASET_HASH",
        "DATASET_STATUS",
        "MODEL_PACKAGE_SHA256",
        "WANDB_RUN_ID",
        "GENERATED_AT",
    ]
    width = max(len(k) for k in keys)
    print("\n🆚 Deployment diff (before → after):")
    any_change = False
    for key in keys:
        b = before.get(key, "")
        a = after.get(key, "")
        b_disp = _short(b, 16) if key == "MODEL_PACKAGE_SHA256" else b or "-"
        a_disp = _short(a, 16) if key == "MODEL_PACKAGE_SHA256" else a or "-"
        marker = " " if b == a else "*"
        if b != a:
            any_change = True
        print(f"   {marker} {key.ljust(width)}  {b_disp or '-'}  →  {a_disp or '-'}")
    if not any_change:
        print(
            "   ⚠️  Nothing changed — the app will keep showing the previous model.\n"
            "      Train a new model, then re-run deploy. If you expected a change,\n"
            "      check that the checkpoint mtime is newer than the existing export."
        )


def _coreml_export_subprocess(
    model_path: Path,
    output_path: Path,
) -> None:
    """Run export_coreml in a fresh subprocess so a native segfault inside
    coremltools doesn't kill the whole CLI.

    Raises RuntimeError with remediation guidance on failure.
    """
    pipeline_root = Path(__file__).resolve().parent.parent
    code = (
        "import sys; sys.path.insert(0, r'" + str(pipeline_root) + "');"
        "from pipeline.export import export_coreml;"
        f"export_coreml(r'{model_path}', r'{output_path}')"
    )
    print(f"   ↪ Running CoreML conversion in isolated subprocess…")
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        for line in proc.stdout.rstrip().splitlines():
            print(f"      {line}")
    if proc.returncode != 0:
        if proc.stderr:
            print("   stderr:")
            for line in proc.stderr.rstrip().splitlines()[-20:]:
                print(f"      {line}")
        # Negative returncode on POSIX = killed by signal (e.g. -11 = SIGSEGV).
        if proc.returncode < 0:
            sig = -proc.returncode
            raise RuntimeError(
                f"CoreML conversion crashed with signal {sig} (likely a torch/coremltools\n"
                "   ABI mismatch). Try an export-only venv with torch==2.7.* and\n"
                "   coremltools>=8.1,<10, then re-run `python main_new.py deploy --force`."
            )
        raise RuntimeError(
            f"CoreML conversion failed (exit {proc.returncode}). See stderr above."
        )


def _latest_registry_metadata(repo_root: Path) -> dict:
    """Return the most recently-created registry metadata dict, if any."""
    runs_root = Path(repo_root) / "02-DataPipeline" / "model_registry" / "runs"
    if not runs_root.exists():
        return {}
    candidates = [p for p in runs_root.iterdir() if p.is_dir() and (p / "metadata.json").exists()]
    if not candidates:
        return {}
    latest = max(candidates, key=lambda p: (p / "metadata.json").stat().st_mtime)
    try:
        with open(latest / "metadata.json", "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def deploy_to_app(
    model_path: Path,
    repo_root: Path,
    exports_dir: Optional[Path] = None,
    xcode_project: Optional[Path] = None,
    force: bool = False,
    skip_coreml: bool = False,
) -> dict[str, object]:
    """
    Deploy trained model and constants to Xcode project.

    This function:
    1. Exports CoreML model to exports/ and copies to Xcode project
    2. Exports normalization JSON to exports/
    3. Generates Swift constants and places in Xcode project's Generated/
    4. Prints a before→after diff so updates are unmistakable.

    Args:
        model_path: Path to trained PyTorch checkpoint
        repo_root: Repository root directory
        exports_dir: Directory for export artifacts (default: exports/)
        xcode_project: Path to Xcode project source directory
        force: Overwrite existing files (always overwrites Generated/ Swift)
        skip_coreml: Skip the .mlpackage rebuild (for debugging Swift constants)

    Returns:
        Dictionary of deployed file paths plus diff metadata.
    """
    model_path = Path(model_path)
    repo_root = Path(repo_root)

    if exports_dir is None:
        exports_dir = repo_root / "02-DataPipeline" / DEFAULT_EXPORTS_DIR
    else:
        exports_dir = Path(exports_dir)

    if xcode_project is None:
        xcode_project = repo_root / DEFAULT_XCODE_PROJECT
    else:
        xcode_project = Path(xcode_project)

    exports_dir.mkdir(parents=True, exist_ok=True)

    print("\n🚀 Deploying model to Xcode project...")
    print(f"   Model:   {model_path}")
    print(f"   Exports: {exports_dir}")
    print(f"   Xcode:   {xcode_project}")

    if not skip_coreml:
        _check_export_env()

    # ---- Snapshot current Generated/NormalizationConstants.swift + mlpackage SHA
    generated_dir = xcode_project / DEFAULT_GENERATED_DIR
    swift_constants = generated_dir / "NormalizationConstants.swift"
    mlpackage_xcode = xcode_project.parent / "ChewNet.mlpackage"

    before = {
        "MODEL_ID": _read_swift_constant(swift_constants, "MODEL_ID"),
        "DATASET_HASH": _read_swift_constant(swift_constants, "DATASET_HASH"),
        "DATASET_STATUS": _read_swift_constant(swift_constants, "DATASET_STATUS"),
        "MODEL_PACKAGE_SHA256": _read_swift_constant(swift_constants, "MODEL_PACKAGE_SHA256")
        or compute_mlpackage_sha256(mlpackage_xcode),
        "WANDB_RUN_ID": _read_swift_constant(swift_constants, "WANDB_RUN_ID"),
        "GENERATED_AT": _read_swift_constant(swift_constants, "GENERATED_AT"),
    }

    deployed: dict[str, object] = {}

    # ---- 1. CoreML export (subprocess-isolated)
    mlpackage_export = exports_dir / "ChewNet.mlpackage"
    if skip_coreml:
        print("   ⚠️  --skip-coreml set; reusing existing exports/ChewNet.mlpackage if present.")
        if not mlpackage_export.exists():
            raise RuntimeError(
                f"--skip-coreml requested but {mlpackage_export} does not exist; "
                "run a full deploy at least once first."
            )
    else:
        if mlpackage_export.exists():
            shutil.rmtree(mlpackage_export)
        _coreml_export_subprocess(model_path, mlpackage_export)
    deployed["mlpackage_export"] = mlpackage_export

    # ---- 2. Copy mlpackage into Xcode project (always overwrite when re-exported)
    if mlpackage_xcode.exists():
        if force or not skip_coreml:
            shutil.rmtree(mlpackage_xcode)
        else:
            print(f"   ⚠️  Skipping (exists, no --force): {mlpackage_xcode}")
    if not mlpackage_xcode.exists():
        shutil.copytree(mlpackage_export, mlpackage_xcode)
        print(f"   ✅ Copied mlpackage: {mlpackage_xcode}")
    deployed["mlpackage_xcode"] = mlpackage_xcode

    # ---- 3. Compute SHA of bundled mlpackage (for traceability in app)
    mlpackage_sha = compute_mlpackage_sha256(mlpackage_xcode)
    if not mlpackage_sha:
        print(f"   ⚠️  Could not compute mlpackage SHA (missing inner model.mlmodel).")
    deployed["model_package_sha256"] = mlpackage_sha

    # ---- 4. Resolve dataset_status from registry metadata (best-effort)
    registry_meta = _latest_registry_metadata(repo_root)
    dataset_status = registry_meta.get("dataset_status") or (
        "registry dataset_manifest available"
        if registry_meta.get("dataset_hash")
        else "no dataset manifest in registry; lineage unknown"
    )
    deployed["dataset_status"] = dataset_status

    # ---- 5. Normalization JSON
    norm_json = exports_dir / "chewnet_norm.json"
    export_normalization_json(model_path, norm_json)
    # Inject SHA + status into the JSON for symmetry with the Swift constants.
    try:
        with open(norm_json, "r") as f:
            norm_data = json.load(f)
        norm_data["model_package_sha256"] = mlpackage_sha
        norm_data["dataset_status"] = dataset_status
        with open(norm_json, "w") as f:
            json.dump(norm_data, f, indent=2)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"   ⚠️  Could not annotate {norm_json}: {exc}")
    deployed["norm_json"] = norm_json

    # ---- 6. Swift constants (always overwrite; this file IS a generated artifact)
    generated_dir.mkdir(parents=True, exist_ok=True)
    generate_swift_constants(
        model_path,
        swift_constants,
        model_package_sha256=mlpackage_sha,
        dataset_status=dataset_status,
    )
    deployed["swift_constants"] = swift_constants

    # ---- 7. Diff snapshot
    after = {
        "MODEL_ID": _read_swift_constant(swift_constants, "MODEL_ID"),
        "DATASET_HASH": _read_swift_constant(swift_constants, "DATASET_HASH"),
        "DATASET_STATUS": _read_swift_constant(swift_constants, "DATASET_STATUS"),
        "MODEL_PACKAGE_SHA256": _read_swift_constant(swift_constants, "MODEL_PACKAGE_SHA256"),
        "WANDB_RUN_ID": _read_swift_constant(swift_constants, "WANDB_RUN_ID"),
        "GENERATED_AT": _read_swift_constant(swift_constants, "GENERATED_AT"),
    }
    deployed["before"] = before
    deployed["after"] = after
    _print_diff_table(before, after)

    sha_unchanged = bool(before["MODEL_PACKAGE_SHA256"]) and (
        before["MODEL_PACKAGE_SHA256"] == after["MODEL_PACKAGE_SHA256"]
    )
    deployed["sha_unchanged"] = sha_unchanged

    print("\n✅ Deployment complete!")
    print("\n📋 Next steps:")
    print("   1. Open the Xcode project")
    print("   2. Product → Clean Build Folder (⇧⌘K) — required for .mlpackage to recompile")
    print("   3. Build & run; open Recording Configuration → Bundled Model")
    print("      to confirm MODEL_ID and short SHA match the values printed above.")

    return deployed


def create_deployment_readme(xcode_project: Path) -> Path:
    """Create a README in the Generated directory explaining the files."""
    generated_dir = Path(xcode_project) / DEFAULT_GENERATED_DIR
    generated_dir.mkdir(parents=True, exist_ok=True)
    
    readme_path = generated_dir / "README.md"
    
    content = '''# Generated Files

⚠️ **Do not edit these files manually!**

These files are auto-generated by the Python pipeline and should be
regenerated whenever you train a new model.

## Files

- `NormalizationConstants.swift` — Feature normalization constants and runtime config

## Regenerating

From the repository root:

```bash
cd 02-DataPipeline
python main.py deploy
```

Or manually:

```bash
python -c "from pipeline import deploy_to_app; deploy_to_app(...)"
```

## Git Tracking

These files ARE tracked in git for convenience. The W&B run ID in the header
provides traceability to the exact training run that produced them.

If you see a diff after pulling, it means someone trained a new model.
'''
    
    with open(readme_path, "w") as f:
        f.write(content)
    
    return readme_path

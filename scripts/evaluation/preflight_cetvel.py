"""Fail-fast checks for the Qwen3.5-4B CETVEL baseline environment."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path

from packaging.version import Version


MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
CETVEL_REVISION = "6119c517e06cce23aaeac103ce3504c9380655e3"
HARNESS_REVISION = "6e49b1f6910931882a4b3b105794c6faf96b74e5"
MINIMUM_VRAM_GIB = 12


def git_revision(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: preflight_cetvel.py CETVEL_DIR MANIFEST_PATH", file=sys.stderr)
        return 2

    cetvel_dir = Path(sys.argv[1]).resolve()
    manifest_path = Path(sys.argv[2]).resolve()
    harness_dir = cetvel_dir / "lm-evaluation-harness"

    failures: list[str] = []
    if git_revision(cetvel_dir) != CETVEL_REVISION:
        failures.append("CETVEL checkout does not match the pinned revision")
    if git_revision(harness_dir) != HARNESS_REVISION:
        failures.append("lm-evaluation-harness does not match the pinned revision")

    try:
        import torch
    except ImportError as error:
        failures.append(f"PyTorch import failed: {error}")
        torch = None

    gpu: dict[str, object] = {"available": False}
    if torch is not None:
        if Version(torch.__version__.split("+")[0]) < Version("2.5"):
            failures.append(
                f"PyTorch {torch.__version__} is incompatible with Transformers "
                "5.17; PyTorch >=2.5 is required"
            )
        if not torch.cuda.is_available():
            failures.append("CUDA is not available")
        else:
            properties = torch.cuda.get_device_properties(0)
            vram_gib = properties.total_memory / 1024**3
            gpu = {
                "available": True,
                "name": properties.name,
                "count": torch.cuda.device_count(),
                "vram_gib": round(vram_gib, 2),
                "bf16_supported": torch.cuda.is_bf16_supported(),
                "cuda_runtime": torch.version.cuda,
            }
            if vram_gib < MINIMUM_VRAM_GIB:
                failures.append(
                    f"GPU has {vram_gib:.2f} GiB VRAM; baseline requires at least "
                    f"{MINIMUM_VRAM_GIB} GiB without quantization"
                )
            if not torch.cuda.is_bf16_supported():
                failures.append("GPU does not report BF16 support")

    transformers_version = package_version("transformers")
    if transformers_version == "not-installed" or Version(transformers_version) < Version("5"):
        failures.append("Transformers v5 or newer is required for Qwen3.5")

    manifest = {
        "purpose": "cetvel-baseline-preflight",
        "model": {
            "repository": "Qwen/Qwen3.5-4B",
            "revision": MODEL_REVISION,
        },
        "cetvel_revision": git_revision(cetvel_dir),
        "harness_revision": git_revision(harness_dir),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            name: package_version(name)
            for name in (
                "torch",
                "torchaudio",
                "torchvision",
                "transformers",
                "lm_eval",
                "datasets",
                "accelerate",
                "sentencepiece",
                "protobuf",
            )
        },
        "gpu": gpu,
        "status": "failed" if failures else "passed",
        "failures": failures,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))

    if failures:
        print("Preflight failed; evaluation was not started.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

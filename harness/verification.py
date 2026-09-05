"""Shared, hardware-independent acceptance checks for diagnostic runners."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def frame_numbers(spec: str) -> list[int]:
    try:
        values = [int(v.strip()) for v in spec.split(",")]
    except ValueError as exc:
        raise ValueError("frames must be comma-separated positive integers") from exc
    if not values or any(v <= 0 for v in values) or values != sorted(set(values)):
        raise ValueError("frames must be positive, unique and strictly increasing")
    return values


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256_file(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def image_signature(path):
    """Include dimensions: equal byte strings can describe different images."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        return {"size": list(im.size), "sha256": hashlib.sha256(im.tobytes()).hexdigest()}


def required_files(directory, names):
    directory = Path(directory)
    missing = [name for name in names
               if not (directory / name).is_file() or (directory / name).stat().st_size == 0]
    if missing:
        raise ValueError("missing or empty artifacts: " + ", ".join(missing))


def compare_arrays(actual, expected, *, tolerance=0, max_mismatches=0):
    """Compare pixels (not channels); thresholds are explicit absolute budgets."""
    import numpy as np
    if tolerance < 0 or max_mismatches < 0:
        raise ValueError("comparison budgets cannot be negative")
    actual, expected = np.asarray(actual), np.asarray(expected)
    if actual.shape != expected.shape or actual.size == 0:
        raise ValueError(f"invalid comparison dimensions: {actual.shape} vs {expected.shape}")
    if actual.ndim not in (2, 3):
        raise ValueError("expected an HxW or HxWxC pixel array")
    delta = np.abs(actual.astype(np.int64) - expected.astype(np.int64))
    if delta.ndim == 3:
        delta = delta.max(axis=2)
    exact = int(np.count_nonzero(delta))
    outside = int(np.count_nonzero(delta > tolerance))
    return {"pixels": int(delta.size), "differing_pixels": exact,
            "exact_percent": float(100 * (delta.size - exact) / delta.size),
            "max_error": int(delta.max()), "tolerance": tolerance,
            "outside_tolerance": outside, "max_mismatches": max_mismatches,
            "passed": outside <= max_mismatches}


def validate_snapshots(directory, frames, returncode, recorded_frames):
    """A complete process, frame receipt and file manifest are all required."""
    if returncode != 0:
        raise ValueError(f"emulator exit code {returncode}")
    if list(recorded_frames) != list(frames):
        raise ValueError(f"snapshot frame receipts differ: expected {frames}, got {recorded_frames}")
    directory = Path(directory)
    expected = [f"frame_{n:08d}.png" for n in frames]
    found = sorted(p.name for p in directory.glob("*.png"))
    if found != expected:
        raise ValueError(f"snapshot manifest differs: expected {expected}, got {found}")
    required_files(directory, expected)
    return {str(n): image_signature(directory / name) for n, name in zip(frames, expected)}

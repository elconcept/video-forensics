from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

WIDTH = 192
HEIGHT = 108


def read_frame(path: Path) -> np.ndarray:
    data = path.read_bytes()
    expected = WIDTH * HEIGHT
    if len(data) != expected:
        raise ValueError(f"invalid normalized frame size: {path}: {len(data)} != {expected}")
    return np.frombuffer(data, dtype=np.uint8).astype(np.float64)


def metrics(left: np.ndarray, right: np.ndarray) -> dict[str, float | None]:
    difference = left - right
    mae = float(np.mean(np.abs(difference)))
    rmse = float(math.sqrt(np.mean(difference * difference)))
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = float(
        math.sqrt(np.sum(left_centered * left_centered) * np.sum(right_centered * right_centered))
    )
    ncc = None if denominator == 0.0 else float(
        np.sum(left_centered * right_centered) / denominator
    )
    identical_fraction = float(np.mean(left == right))
    return {
        "mae": round(mae, 9),
        "rmse": round(rmse, 9),
        "ncc": None if ncc is None else round(ncc, 9),
        "identical_pixel_fraction": round(identical_fraction, 9),
    }


def compare(root: Path, output: Path) -> dict[str, object]:
    directories = sorted(path.parent for path in root.glob("*_perceptual/manifest.json"))
    if len(directories) < 2:
        raise ValueError("at least two perceptual decoder runs are required")
    manifests = {
        directory.name: json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        for directory in directories
    }
    input_hashes = {
        manifest.get("input", {}).get("sha256") for manifest in manifests.values()
    }
    if None in input_hashes or len(input_hashes) != 1:
        raise ValueError("perceptual runs do not share one verified input SHA-256")
    runs = {
        directory.name: sorted((directory / "frames").glob("frame_*.gray"))
        for directory in directories
    }
    pairs: list[dict[str, object]] = []
    first_divergence: int | None = None
    for left_id, right_id in itertools.combinations(runs, 2):
        left_frames = runs[left_id]
        right_frames = runs[right_id]
        maximum = max(len(left_frames), len(right_frames))
        frame_rows: list[dict[str, object]] = []
        for index in range(maximum):
            if index >= len(left_frames) or index >= len(right_frames):
                row = {"frame_number": index + 1, "status": "missing_in_one_run"}
            else:
                row = {
                    "frame_number": index + 1,
                    "status": "compared",
                    **metrics(read_frame(left_frames[index]), read_frame(right_frames[index])),
                }
            if first_divergence is None and (
                row["status"] != "compared" or row.get("mae") != 0.0
            ):
                first_divergence = index + 1
            frame_rows.append(row)
        pairs.append({"left": left_id, "right": right_id, "frames": frame_rows})

    result: dict[str, object] = {
        "schema_version": 1,
        "input_sha256": next(iter(input_hashes)),
        "normalization": {"width": WIDTH, "height": HEIGHT, "pixel_format": "gray"},
        "run_ids": list(runs),
        "frame_counts": {name: len(paths) for name, paths in runs.items()},
        "first_perceptual_divergence": first_divergence,
        "pairs": pairs,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "perceptual_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="compare-perceptual-runs")
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = compare(args.root.resolve(strict=True), args.output.resolve())
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "frame_counts": result["frame_counts"],
        "first_perceptual_divergence": result["first_perceptual_divergence"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

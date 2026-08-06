from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

COMPARE_WIDTH = 96
COMPARE_HEIGHT = 54


def load_luma(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float64)


def resize(array: np.ndarray, width: int, height: int) -> np.ndarray:
    image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="L")
    return np.asarray(
        image.resize((width, height), Image.Resampling.LANCZOS),
        dtype=np.float64,
    )


def ncc(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.shape != right.shape:
        raise ValueError(f"array shape differs: {left.shape} != {right.shape}")
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = float(
        math.sqrt(
            np.sum(left_centered * left_centered)
            * np.sum(right_centered * right_centered)
        )
    )
    if denominator == 0.0:
        return None
    return float(np.sum(left_centered * right_centered) / denominator)


def crop(array: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("invalid crop geometry")
    if y + height > array.shape[0] or x + width > array.shape[1]:
        raise ValueError("crop exceeds screen-frame bounds")
    return array[y : y + height, x : x + width]


def calibrate(
    screen: np.ndarray,
    reference: np.ndarray,
    *,
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    width_min: int,
    width_max: int,
    step: int,
    aspect_ratio: float,
) -> dict[str, object]:
    if step <= 0:
        raise ValueError("calibration step must be positive")
    target = resize(reference, COMPARE_WIDTH, COMPARE_HEIGHT)
    best: dict[str, object] | None = None
    tested = 0
    for width in range(width_min, width_max + 1, step):
        height = max(1, round(width / aspect_ratio))
        for y in range(y_min, y_max + 1, step):
            for x in range(x_min, x_max + 1, step):
                if y + height > screen.shape[0] or x + width > screen.shape[1]:
                    continue
                candidate = resize(crop(screen, x, y, width, height), COMPARE_WIDTH, COMPARE_HEIGHT)
                score = ncc(candidate, target)
                tested += 1
                if score is None:
                    continue
                if best is None or score > float(best["ncc"]):
                    best = {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "ncc": round(score, 9),
                    }
    if best is None:
        raise ValueError("calibration produced no comparable crop")
    best["tested_crop_count"] = tested
    return best


def candidate_frames(root: Path) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for source in sorted(path for path in root.iterdir() if path.is_dir()):
        for frame in sorted(
            path
            for path in source.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        ):
            rows.append((source.name, frame))
    if not rows:
        raise ValueError(f"no candidate frames found: {root}")
    return rows


def compare_screen_frames(
    screen_root: Path,
    candidates_root: Path,
    calibration: dict[str, object],
) -> list[dict[str, object]]:
    screen_paths = sorted(
        path
        for path in screen_root.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    )
    if not screen_paths:
        raise ValueError(f"no screen frames found: {screen_root}")
    candidates = candidate_frames(candidates_root)
    prepared = [
        (source, path, resize(load_luma(path), COMPARE_WIDTH, COMPARE_HEIGHT))
        for source, path in candidates
    ]
    rows: list[dict[str, object]] = []
    for screen_number, screen_path in enumerate(screen_paths, start=1):
        screen = load_luma(screen_path)
        fixed = crop(
            screen,
            int(calibration["x"]),
            int(calibration["y"]),
            int(calibration["width"]),
            int(calibration["height"]),
        )
        fixed = resize(fixed, COMPARE_WIDTH, COMPARE_HEIGHT)
        scores: list[tuple[float, str, Path]] = []
        for source, path, candidate in prepared:
            score = ncc(fixed, candidate)
            if score is not None:
                scores.append((score, source, path))
        scores.sort(reverse=True, key=lambda item: item[0])
        if not scores:
            raise ValueError(f"no comparable candidates for screen frame: {screen_path}")
        best = scores[0]
        runner_up = scores[1] if len(scores) > 1 else None
        rows.append(
            {
                "screen_frame_number": screen_number,
                "screen_file": screen_path.name,
                "best_source": best[1],
                "best_candidate_file": best[2].name,
                "best_ncc": round(best[0], 9),
                "runner_up_source": None if runner_up is None else runner_up[1],
                "runner_up_candidate_file": None if runner_up is None else runner_up[2].name,
                "runner_up_ncc": None if runner_up is None else round(runner_up[0], 9),
                "ncc_margin": None if runner_up is None else round(best[0] - runner_up[0], 9),
                "candidate_count": len(scores),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(
    control_screen: Path,
    control_reference: Path,
    screen_root: Path,
    candidates_root: Path,
    output: Path,
    *,
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    width_min: int,
    width_max: int,
    step: int,
) -> dict[str, object]:
    control_screen = control_screen.expanduser().resolve(strict=True)
    control_reference = control_reference.expanduser().resolve(strict=True)
    screen_root = screen_root.expanduser().resolve(strict=True)
    candidates_root = candidates_root.expanduser().resolve(strict=True)
    reference = load_luma(control_reference)
    calibration = calibrate(
        load_luma(control_screen),
        reference,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        width_min=width_min,
        width_max=width_max,
        step=step,
        aspect_ratio=reference.shape[1] / reference.shape[0],
    )
    rows = compare_screen_frames(screen_root, candidates_root, calibration)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "matches.csv", rows)
    result: dict[str, object] = {
        "schema_version": 1,
        "module": "playback_divergence",
        "calibration": calibration,
        "control": {
            "screen": str(control_screen),
            "reference": str(control_reference),
        },
        "screen_root": str(screen_root),
        "candidates_root": str(candidates_root),
        "screen_frame_count": len(rows),
        "matches": rows,
        "interpretation_boundary": (
            "Crop geometry was calibrated on one known control pair and frozen for all comparisons. "
            "Candidate matching is unconstrained across every supplied candidate frame. NCC is an "
            "observation and does not identify source provenance without further validation."
        ),
    }
    (output / "playback_divergence.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-playback-divergence")
    parser.add_argument("--control-screen", required=True, type=Path)
    parser.add_argument("--control-reference", required=True, type=Path)
    parser.add_argument("--screen-root", required=True, type=Path)
    parser.add_argument("--candidates-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--x-min", required=True, type=int)
    parser.add_argument("--x-max", required=True, type=int)
    parser.add_argument("--y-min", required=True, type=int)
    parser.add_argument("--y-max", required=True, type=int)
    parser.add_argument("--width-min", required=True, type=int)
    parser.add_argument("--width-max", required=True, type=int)
    parser.add_argument("--step", type=int, default=2)
    args = parser.parse_args()
    try:
        result = analyze(
            args.control_screen,
            args.control_reference,
            args.screen_root,
            args.candidates_root,
            args.output,
            x_min=args.x_min,
            x_max=args.x_max,
            y_min=args.y_min,
            y_max=args.y_max,
            width_min=args.width_min,
            width_max=args.width_max,
            step=args.step,
        )
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"calibration": result["calibration"], "screen_frame_count": result["screen_frame_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

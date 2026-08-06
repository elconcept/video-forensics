from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

DEFAULT_MIN_REGION_PIXELS = 64
DEFAULT_GLOBAL_MOTION_THRESHOLD = 2.0


def load_gray(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.uint8)


def connected_regions(mask: np.ndarray, minimum_pixels: int) -> list[dict[str, int]]:
    if mask.ndim != 2:
        raise ValueError("connected-region mask must be two-dimensional")
    if minimum_pixels <= 0:
        raise ValueError("minimum region size must be positive")
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    regions: list[dict[str, int]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[y, x] = True
            count = 0
            x_min = x_max = x
            y_min = y_max = y
            while queue:
                current_x, current_y = queue.popleft()
                count += 1
                x_min = min(x_min, current_x)
                x_max = max(x_max, current_x)
                y_min = min(y_min, current_y)
                y_max = max(y_max, current_y)
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if (
                        0 <= next_x < width
                        and 0 <= next_y < height
                        and mask[next_y, next_x]
                        and not visited[next_y, next_x]
                    ):
                        visited[next_y, next_x] = True
                        queue.append((next_x, next_y))
            if count >= minimum_pixels:
                regions.append(
                    {
                        "pixel_count": count,
                        "x": x_min,
                        "y": y_min,
                        "width": x_max - x_min + 1,
                        "height": y_max - y_min + 1,
                    }
                )
    return sorted(regions, key=lambda region: -region["pixel_count"])


def analyze_pair(
    previous: np.ndarray,
    current: np.ndarray,
    *,
    minimum_pixels: int,
    global_motion_threshold: float,
) -> dict[str, object]:
    if previous.shape != current.shape:
        raise ValueError(f"frame geometry differs: {previous.shape} != {current.shape}")
    absolute = np.abs(current.astype(np.int16) - previous.astype(np.int16))
    global_mae = float(np.mean(absolute))
    static_mask = absolute == 0
    regions = connected_regions(static_mask, minimum_pixels)
    return {
        "global_mae": round(global_mae, 9),
        "global_motion_present": global_mae >= global_motion_threshold,
        "bit_identical_pixel_fraction": round(float(np.mean(static_mask)), 9),
        "region_count": len(regions),
        "regions": regions,
        "candidate": global_mae >= global_motion_threshold and bool(regions),
    }


def frame_paths(root: Path) -> list[Path]:
    paths = sorted(
        path
        for path in root.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    )
    if len(paths) < 2:
        raise ValueError("at least two image frames are required")
    return paths


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    columns = [
        "previous_frame",
        "current_frame",
        "global_mae",
        "global_motion_present",
        "bit_identical_pixel_fraction",
        "region_count",
        "candidate",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in columns})


def analyze(
    frames_root: Path,
    output: Path,
    *,
    minimum_pixels: int = DEFAULT_MIN_REGION_PIXELS,
    global_motion_threshold: float = DEFAULT_GLOBAL_MOTION_THRESHOLD,
    host_profile_id: str | None = None,
) -> dict[str, object]:
    frames_root = frames_root.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    paths = frame_paths(frames_root)
    rows: list[dict[str, object]] = []
    previous = load_gray(paths[0])
    for index, current_path in enumerate(paths[1:], start=1):
        current = load_gray(current_path)
        pair = analyze_pair(
            previous,
            current,
            minimum_pixels=minimum_pixels,
            global_motion_threshold=global_motion_threshold,
        )
        rows.append(
            {
                "previous_frame": paths[index - 1].name,
                "current_frame": current_path.name,
                **pair,
            }
        )
        previous = current

    findings = [
        {
            "id": "STATIC_REGION_WITH_GLOBAL_MOTION",
            "severity": "medium",
            "description": (
                "A connected region remained bit-identical between consecutive decoded frames "
                "while mean absolute change across the complete frame exceeded the configured threshold."
            ),
            "evidence_refs": [
                f"static_region_motion/pairs.json#pair-{index + 1}"
            ],
            "requires_reference": False,
            "host_profile": host_profile_id,
            "observations": row,
            "mundane_explanation": (
                "Static overlays, masked areas, compression plateaus, or genuinely motionless scene "
                "content can produce identical regions. The finding requires visual and codec-level review."
            ),
        }
        for index, row in enumerate(rows)
        if row["candidate"]
    ]
    result: dict[str, object] = {
        "schema_version": 1,
        "module": "static_region_motion",
        "parameters": {
            "minimum_region_pixels": minimum_pixels,
            "global_motion_mae_threshold": global_motion_threshold,
            "connectivity": 4,
            "static_rule": "decoded grayscale pixels exactly equal",
        },
        "frame_count": len(paths),
        "pair_count": len(rows),
        "finding_count": len(findings),
        "pairs": rows,
        "findings": findings,
        "interpretation_boundary": (
            "The module operates on decoded pixels. Results remain decoder-dependent when the "
            "encoded stream contains missing references or concealment."
        ),
    }
    write_csv(output / "pairs.csv", rows)
    (output / "pairs.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "static_region_motion.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-static-region-motion")
    parser.add_argument("frames_root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-region-pixels", type=int, default=DEFAULT_MIN_REGION_PIXELS)
    parser.add_argument(
        "--global-motion-threshold", type=float, default=DEFAULT_GLOBAL_MOTION_THRESHOLD
    )
    parser.add_argument("--host-profile-id")
    args = parser.parse_args()
    try:
        result = analyze(
            args.frames_root,
            args.output,
            minimum_pixels=args.minimum_region_pixels,
            global_motion_threshold=args.global_motion_threshold,
            host_profile_id=args.host_profile_id,
        )
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"finding_count": result["finding_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

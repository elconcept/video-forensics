from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def overlap(left: dict[str, int], right: dict[str, int]) -> float:
    x1 = max(left["x"], right["x"])
    y1 = max(left["y"], right["y"])
    x2 = min(left["x"] + left["width"], right["x"] + right["width"])
    y2 = min(left["y"] + left["height"], right["y"] + right["height"])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    intersection = (x2 - x1) * (y2 - y1)
    union = (
        left["width"] * left["height"]
        + right["width"] * right["height"]
        - intersection
    )
    return intersection / union


def candidate_regions(pairs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for pair_number, pair in enumerate(pairs, start=1):
        if not pair.get("candidate"):
            continue
        for region_number, region in enumerate(pair.get("regions", []), start=1):
            rows.append(
                {
                    "pair_number": pair_number,
                    "previous_frame": pair["previous_frame"],
                    "current_frame": pair["current_frame"],
                    "global_mae": pair["global_mae"],
                    "region_number": region_number,
                    "region": region,
                }
            )
    return rows


def build_series(
    pairs: list[dict[str, object]],
    *,
    minimum_iou: float,
    minimum_length: int,
) -> list[dict[str, object]]:
    if not 0.0 <= minimum_iou <= 1.0:
        raise ValueError("minimum IoU must be between zero and one")
    if minimum_length < 1:
        raise ValueError("minimum series length must be positive")
    active: list[dict[str, object]] = []
    completed: list[dict[str, object]] = []
    for item in candidate_regions(pairs):
        pair_number = int(item["pair_number"])
        region = item["region"]
        best: dict[str, object] | None = None
        best_iou = 0.0
        for series in active:
            if int(series["end_pair"]) != pair_number - 1:
                continue
            score = overlap(series["last_region"], region)
            if score >= minimum_iou and score > best_iou:
                best = series
                best_iou = score
        if best is None:
            active.append(
                {
                    "start_pair": pair_number,
                    "end_pair": pair_number,
                    "entries": [item],
                    "last_region": region,
                }
            )
        else:
            best["end_pair"] = pair_number
            best["entries"].append(item)
            best["last_region"] = region

        stale = [series for series in active if int(series["end_pair"]) < pair_number - 1]
        for series in stale:
            completed.append(series)
            active.remove(series)
    completed.extend(active)

    results: list[dict[str, object]] = []
    for series in completed:
        entries = series["entries"]
        if len(entries) < minimum_length:
            continue
        x_min = min(int(entry["region"]["x"]) for entry in entries)
        y_min = min(int(entry["region"]["y"]) for entry in entries)
        x_max = max(
            int(entry["region"]["x"]) + int(entry["region"]["width"])
            for entry in entries
        )
        y_max = max(
            int(entry["region"]["y"]) + int(entry["region"]["height"])
            for entry in entries
        )
        results.append(
            {
                "series_number": len(results) + 1,
                "start_pair": series["start_pair"],
                "end_pair": series["end_pair"],
                "length_pairs": len(entries),
                "start_frame": entries[0]["previous_frame"],
                "end_frame": entries[-1]["current_frame"],
                "union_box": {
                    "x": x_min,
                    "y": y_min,
                    "width": x_max - x_min,
                    "height": y_max - y_min,
                },
                "minimum_global_mae": min(float(entry["global_mae"]) for entry in entries),
                "maximum_global_mae": max(float(entry["global_mae"]) for entry in entries),
                "entries": entries,
            }
        )
    return results


def save_review_images(
    frames_root: Path,
    output: Path,
    series: list[dict[str, object]],
    padding: int,
) -> list[dict[str, object]]:
    frame_lookup = {path.name: path for path in frames_root.iterdir() if path.is_file()}
    assets: list[dict[str, object]] = []
    for item in series:
        box = item["union_box"]
        series_dir = output / f"series_{int(item['series_number']):04d}"
        series_dir.mkdir(parents=True, exist_ok=False)
        for entry in item["entries"]:
            frame_name = str(entry["current_frame"])
            source = frame_lookup.get(frame_name)
            if source is None:
                continue
            with Image.open(source) as image:
                rgb = image.convert("RGB")
                x1 = max(0, int(box["x"]) - padding)
                y1 = max(0, int(box["y"]) - padding)
                x2 = min(rgb.width, int(box["x"]) + int(box["width"]) + padding)
                y2 = min(rgb.height, int(box["y"]) + int(box["height"]) + padding)
                crop = rgb.crop((x1, y1, x2, y2))
                draw = ImageDraw.Draw(crop)
                draw.rectangle(
                    (
                        int(box["x"]) - x1,
                        int(box["y"]) - y1,
                        int(box["x"]) + int(box["width"]) - x1 - 1,
                        int(box["y"]) + int(box["height"]) - y1 - 1,
                    ),
                    outline=(255, 0, 0),
                    width=2,
                )
                filename = f"pair_{int(entry['pair_number']):04d}_{frame_name}.png"
                target = series_dir / filename
                crop.save(target, format="PNG")
                assets.append(
                    {
                        "series_number": item["series_number"],
                        "pair_number": entry["pair_number"],
                        "source_frame": frame_name,
                        "file": str(target.relative_to(output)),
                    }
                )
    return assets


def analyze(
    pairs_json: Path,
    frames_root: Path,
    output: Path,
    *,
    minimum_iou: float,
    minimum_length: int,
    padding: int,
    host_profile_id: str | None,
) -> dict[str, object]:
    pairs_json = pairs_json.expanduser().resolve(strict=True)
    frames_root = frames_root.expanduser().resolve(strict=True)
    pairs = json.loads(pairs_json.read_text(encoding="utf-8"))
    if not isinstance(pairs, list):
        raise TypeError("pairs JSON must contain a list")
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    series = build_series(
        pairs,
        minimum_iou=minimum_iou,
        minimum_length=minimum_length,
    )
    assets = save_review_images(frames_root, output / "review", series, padding)
    findings = [
        {
            "id": "STATIC_REGION_SERIES_WITH_GLOBAL_MOTION",
            "severity": "medium",
            "description": "A spatially overlapping bit-identical region persisted across consecutive frame pairs while global frame change remained non-zero.",
            "evidence_refs": [
                f"static_region_series/series.json#series-{item['series_number']}",
                f"static_region_series/review/series_{int(item['series_number']):04d}",
            ],
            "requires_reference": False,
            "host_profile": host_profile_id,
            "observations": item,
            "mundane_explanation": "Static overlays, masks, compression plateaus, or genuinely motionless scene regions can persist through surrounding motion.",
        }
        for item in series
    ]
    result: dict[str, object] = {
        "schema_version": 1,
        "module": "static_region_series",
        "parameters": {
            "minimum_iou": minimum_iou,
            "minimum_length_pairs": minimum_length,
            "review_crop_padding": padding,
        },
        "series_count": len(series),
        "review_asset_count": len(assets),
        "series": series,
        "review_assets": assets,
        "findings": findings,
        "interpretation_boundary": (
            "Series are linked by bounding-box overlap in decoded grayscale output. "
            "They remain decoder-dependent where concealment or missing references occur."
        ),
    }
    (output / "series.json").write_text(
        json.dumps(series, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "static_region_series.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-static-region-series")
    parser.add_argument("pairs_json", type=Path)
    parser.add_argument("--frames-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-iou", type=float, default=0.5)
    parser.add_argument("--minimum-length", type=int, default=2)
    parser.add_argument("--padding", type=int, default=16)
    parser.add_argument("--host-profile-id")
    args = parser.parse_args()
    try:
        result = analyze(
            args.pairs_json,
            args.frames_root,
            args.output,
            minimum_iou=args.minimum_iou,
            minimum_length=args.minimum_length,
            padding=args.padding,
            host_profile_id=args.host_profile_id,
        )
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"series_count": result["series_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

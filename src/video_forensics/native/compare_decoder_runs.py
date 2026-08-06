from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ERROR_PATTERNS = {
    "missing_reference": re.compile(r"Could not find ref with POC\s+(-?\d+)", re.IGNORECASE),
    "decode_failure": re.compile(r"decode|decoding|invalid data|error", re.IGNORECASE),
    "hardware_device": re.compile(r"d3d11va|qsv|cuda|nvdec|cuvid|videotoolbox", re.IGNORECASE),
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return payload


def parse_framemd5(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 6:
                continue
            rows.append(
                {
                    "frame_number": len(rows) + 1,
                    "stream_index": parts[0],
                    "dts": parts[1],
                    "pts": parts[2],
                    "duration": parts[3],
                    "size": parts[4],
                    "hash": parts[5],
                }
            )
    return rows


def inspect_run(directory: Path) -> dict[str, Any]:
    manifest = read_json(directory / "manifest.json")
    stderr_path = directory / "stderr.txt"
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.is_file() else ""
    frames = parse_framemd5(directory / "frames.framemd5")
    missing_pocs = [
        int(match.group(1)) for match in ERROR_PATTERNS["missing_reference"].finditer(stderr)
    ]
    hardware_lines = [
        line for line in stderr.splitlines() if ERROR_PATTERNS["hardware_device"].search(line)
    ]
    return {
        "run_id": directory.name,
        "directory": str(directory),
        "profile": manifest.get("profile", {}),
        "status": manifest.get("status"),
        "input_sha256": manifest.get("input", {}).get("sha256"),
        "returncode": manifest.get("decode", {}).get("returncode"),
        "frame_count": len(frames),
        "frames": frames,
        "missing_reference_pocs": missing_pocs,
        "hardware_log_lines": hardware_lines,
    }


def validate_inputs(runs: list[dict[str, Any]]) -> None:
    hashes = {run.get("input_sha256") for run in runs}
    if None in hashes or len(hashes) != 1:
        raise ValueError("decoder runs do not share one verified input SHA-256")


def compare_frames(runs: list[dict[str, Any]]) -> list[dict[str, object]]:
    max_frames = max((int(run["frame_count"]) for run in runs), default=0)
    rows: list[dict[str, object]] = []
    for frame_number in range(1, max_frames + 1):
        hashes: dict[str, str | None] = {}
        pts: dict[str, str | None] = {}
        for run in runs:
            frames = run["frames"]
            frame = frames[frame_number - 1] if frame_number <= len(frames) else None
            hashes[str(run["run_id"])] = None if frame is None else str(frame["hash"])
            pts[str(run["run_id"])] = None if frame is None else str(frame["pts"])
        available = [value for value in hashes.values() if value is not None]
        rows.append(
            {
                "frame_number": frame_number,
                "available_run_count": len(available),
                "distinct_hash_count": len(set(available)),
                "all_available_hashes_equal": bool(available) and len(set(available)) == 1,
                "hashes": hashes,
                "pts": pts,
            }
        )
    return rows


def first_divergence(rows: list[dict[str, object]], run_count: int) -> int | None:
    for row in rows:
        if (
            int(row["available_run_count"]) != run_count
            or int(row["distinct_hash_count"]) > 1
        ):
            return int(row["frame_number"])
    return None


def write_csv(path: Path, runs: list[dict[str, Any]], rows: list[dict[str, object]]) -> None:
    run_ids = [str(run["run_id"]) for run in runs]
    columns = [
        "frame_number",
        "available_run_count",
        "distinct_hash_count",
        "all_available_hashes_equal",
        *[f"hash_{run_id}" for run_id in run_ids],
        *[f"pts_{run_id}" for run_id in run_ids],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            flattened: dict[str, object] = {
                "frame_number": row["frame_number"],
                "available_run_count": row["available_run_count"],
                "distinct_hash_count": row["distinct_hash_count"],
                "all_available_hashes_equal": row["all_available_hashes_equal"],
            }
            hashes = row["hashes"]
            pts = row["pts"]
            for run_id in run_ids:
                flattened[f"hash_{run_id}"] = hashes.get(run_id)
                flattened[f"pts_{run_id}"] = pts.get(run_id)
            writer.writerow(flattened)


def compare(input_root: Path, output: Path) -> dict[str, object]:
    directories = sorted(path.parent for path in input_root.glob("*/manifest.json"))
    if len(directories) < 2:
        raise ValueError("at least two decoder-run directories are required")
    runs = [inspect_run(directory) for directory in directories]
    validate_inputs(runs)
    rows = compare_frames(runs)
    divergence = first_divergence(rows, len(runs))
    frame_counts = {str(run["run_id"]): int(run["frame_count"]) for run in runs}
    missing = {
        str(run["run_id"]): list(run["missing_reference_pocs"])
        for run in runs
    }
    result: dict[str, object] = {
        "schema_version": 1,
        "input_sha256": runs[0]["input_sha256"],
        "run_count": len(runs),
        "run_ids": [run["run_id"] for run in runs],
        "frame_counts": frame_counts,
        "frame_count_distribution": dict(sorted(Counter(frame_counts.values()).items())),
        "first_divergent_frame": divergence,
        "missing_reference_pocs": missing,
        "runs": [
            {key: value for key, value in run.items() if key != "frames"}
            for run in runs
        ],
        "frame_comparison": rows,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "decoder_matrix.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(output / "frame_comparison.csv", runs, rows)
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="compare-decoder-runs")
    result.add_argument("input_root", type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = compare(args.input_root.resolve(strict=True), args.output.resolve())
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "run_count": result["run_count"],
        "first_divergent_frame": result["first_divergent_frame"],
        "frame_counts": result["frame_counts"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

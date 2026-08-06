from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def read_hashes(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row["sha256"] for row in csv.DictReader(handle)]


def compare(root: Path, output: Path) -> dict[str, object]:
    directories = sorted(path.parent for path in root.glob("*_normalized/manifest.json"))
    if len(directories) < 2:
        raise ValueError("at least two normalized decoder runs are required")
    runs = {directory.name: read_hashes(directory / "normalized_hashes.csv") for directory in directories}
    maximum = max(len(values) for values in runs.values())
    rows: list[dict[str, object]] = []
    for index in range(maximum):
        hashes = {
            run_id: values[index] if index < len(values) else None
            for run_id, values in runs.items()
        }
        available = [value for value in hashes.values() if value is not None]
        rows.append(
            {
                "frame_number": index + 1,
                "available_run_count": len(available),
                "distinct_hash_count": len(set(available)),
                "all_equal": len(available) == len(runs) and len(set(available)) == 1,
                "hashes": hashes,
            }
        )
    first = next((int(row["frame_number"]) for row in rows if not row["all_equal"]), None)
    result: dict[str, object] = {
        "schema_version": 1,
        "run_ids": list(runs),
        "frame_counts": {name: len(values) for name, values in runs.items()},
        "first_normalized_divergence": first,
        "frames": rows,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "normalized_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="compare-normalized-runs")
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
        "first_normalized_divergence": result["first_normalized_divergence"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

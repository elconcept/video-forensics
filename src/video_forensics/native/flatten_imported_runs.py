from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return payload


def discover(imported_root: Path) -> list[tuple[str, Path]]:
    discovered: list[tuple[str, Path]] = []
    for receipt_path in sorted(imported_root.glob("*/import_receipt.json")):
        source_root = receipt_path.parent
        receipt = read_json(receipt_path)
        source_id = str(receipt["source_id"])
        for manifest_path in sorted(source_root.glob("*/manifest.json")):
            run_dir = manifest_path.parent
            if run_dir.name.endswith("_perceptual"):
                continue
            discovered.append((source_id, run_dir))
    return discovered


def link_or_copy(source: Path, destination: Path, copy: bool) -> str:
    if copy:
        shutil.copytree(source, destination)
        return "copy"
    try:
        os.symlink(source, destination, target_is_directory=True)
        return "symlink"
    except OSError:
        shutil.copytree(source, destination)
        return "copy_fallback"


def flatten(imported_root: Path, destination: Path, *, copy: bool = False) -> dict[str, object]:
    imported_root = imported_root.resolve(strict=True)
    if not imported_root.is_dir():
        raise ValueError(f"imported root is not a directory: {imported_root}")
    discovered = discover(imported_root)
    if not discovered:
        raise ValueError(f"no imported decoder runs found: {imported_root}")

    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    entries: list[dict[str, object]] = []
    names: set[str] = set()
    for source_id, run_dir in discovered:
        run_name = f"{source_id}__{run_dir.name}"
        if run_name in names:
            raise ValueError(f"duplicate flattened run name: {run_name}")
        names.add(run_name)
        target = destination / run_name
        method = link_or_copy(run_dir, target, copy)
        entries.append(
            {
                "source_id": source_id,
                "original_run": run_dir.name,
                "flattened_run": run_name,
                "source_path": str(run_dir),
                "target_path": str(target),
                "method": method,
            }
        )

    manifest = {
        "schema_version": 1,
        "imported_root": str(imported_root),
        "destination": str(destination),
        "run_count": len(entries),
        "runs": entries,
    }
    (destination / "flatten_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="flatten-imported-runs")
    parser.add_argument("imported_root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--copy", action="store_true")
    args = parser.parse_args()
    try:
        result = flatten(args.imported_root, args.output, copy=args.copy)
    except (FileNotFoundError, FileExistsError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"run_count": result["run_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

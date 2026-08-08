from __future__ import annotations

import csv
import json
from pathlib import Path

from video_forensics.native.compare_normalized_runs import compare


def make_run(root: Path, name: str, hashes: list[str]) -> None:
    directory = root / f"{name}_normalized"
    directory.mkdir()
    (directory / "manifest.json").write_text("{}", encoding="utf-8")
    with (directory / "normalized_hashes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["frame_number", "sha256"])
        writer.writeheader()
        for number, digest in enumerate(hashes, start=1):
            writer.writerow({"frame_number": number, "sha256": digest})


def test_compare_finds_normalized_divergence(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    root.mkdir()
    make_run(root, "a", ["x", "y"])
    make_run(root, "b", ["x", "z"])
    result = compare(root, tmp_path / "comparison")
    assert result["first_normalized_divergence"] == 2
    saved = json.loads((tmp_path / "comparison" / "normalized_comparison.json").read_text())
    assert saved["frame_counts"] == {"a_normalized": 2, "b_normalized": 2}

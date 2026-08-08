from __future__ import annotations

import json
from pathlib import Path

from video_forensics.native.cross_run_compare import analyze


def write_run(root: Path, timestamp: str, frame_count: int) -> None:
    run = root / timestamp / "decoder"
    run.mkdir(parents=True)
    (run / "result.json").write_text(
        json.dumps(
            {
                "module": "decoder",
                "status": "completed",
                "input": {"sha256": "same-source"},
                "frame_count": frame_count,
                "findings": [],
            }
        ),
        encoding="utf-8",
    )


def test_compares_all_timestamp_directories(tmp_path: Path) -> None:
    root = tmp_path / "recording"
    root.mkdir()
    write_run(root, "20260806T120000Z", 192)
    write_run(root, "20260806T130000Z", 236)
    result = analyze(root)
    assert result["run_count"] == 2
    assert result["comparison"]["different_module_count"] == 1
    assert (root / "cross_run_comparison" / "COMPARISON.md").is_file()
    assert (root / "cross_run_comparison" / "comparison.json").is_file()


def test_ignores_non_timestamp_directories(tmp_path: Path) -> None:
    root = tmp_path / "recording"
    root.mkdir()
    write_run(root, "20260806T120000Z", 192)
    (root / "cross_run_comparison").mkdir()
    result = analyze(root)
    assert result["run_count"] == 1

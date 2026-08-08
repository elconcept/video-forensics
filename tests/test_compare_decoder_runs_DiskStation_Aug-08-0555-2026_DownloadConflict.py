from __future__ import annotations

import json
from pathlib import Path

import pytest

from video_forensics.native.compare_decoder_runs import compare, parse_framemd5


def make_run(root: Path, name: str, hashes: list[str], input_hash: str = "abc") -> None:
    directory = root / name
    directory.mkdir(parents=True)
    manifest = {
        "status": "completed",
        "input": {"sha256": input_hash},
        "decode": {"returncode": 0},
        "profile": {"profile_id": name},
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    lines = ["#format: frame checksums"]
    lines.extend(f"0, {index}, {index}, 1, 10, {digest}" for index, digest in enumerate(hashes))
    (directory / "frames.framemd5").write_text("\n".join(lines), encoding="utf-8")
    (directory / "stderr.txt").write_text("", encoding="utf-8")


def test_parse_framemd5(tmp_path: Path) -> None:
    path = tmp_path / "frames.framemd5"
    path.write_text("# header\n0, 0, 0, 1, 10, abc\n", encoding="utf-8")
    assert parse_framemd5(path)[0]["hash"] == "abc"


def test_compare_detects_first_divergence(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    make_run(runs, "a", ["x", "y", "z"])
    make_run(runs, "b", ["x", "q", "z"])
    result = compare(runs, tmp_path / "comparison")
    assert result["first_divergent_frame"] == 2
    assert result["frame_counts"] == {"a": 3, "b": 3}


def test_compare_rejects_different_inputs(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    make_run(runs, "a", ["x"], "one")
    make_run(runs, "b", ["x"], "two")
    with pytest.raises(ValueError, match="SHA-256"):
        compare(runs, tmp_path / "comparison")

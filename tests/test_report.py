from __future__ import annotations

import json
from pathlib import Path

from video_forensics.tools.report import (
    _load_finding_counts,
    _render_markdown,
    _stage_table,
)


def test_stage_table_records_completed_and_missing_stages() -> None:
    lines = _stage_table({"integrity": {}}, ["metadata"], {"timeline": 2})
    assert "| integrity | completed | 0 |" in lines
    assert "| timeline | not run | 2 |" in lines


def test_load_finding_counts(tmp_path: Path) -> None:
    timeline = tmp_path / "timeline"
    timeline.mkdir()
    (timeline / "anomalies.json").write_text(
        json.dumps([{"kind": "duplicate_pts"}, {"kind": "missing_pts"}]),
        encoding="utf-8",
    )
    assert _load_finding_counts(tmp_path)["timeline"] == 2


def test_render_markdown_contains_hash_and_stage_status() -> None:
    manifest = {
        "application": {"name": "video-forensics", "version": "0.1.0"},
        "run": {"status": "completed"},
        "input": {"path": "/evidence/test.mov", "size_bytes": 10},
    }
    stages = {
        "integrity": {
            "hashes": {"sha256": "abc", "sha512": "def"},
            "input_unchanged_during_read": True,
        }
    }
    report = _render_markdown(manifest, stages, ["metadata"], {"timeline": 2})
    assert "SHA-256: `abc`" in report
    assert "| integrity | completed | 0 |" in report
    assert "`timeline`: 2 observation record(s)." in report

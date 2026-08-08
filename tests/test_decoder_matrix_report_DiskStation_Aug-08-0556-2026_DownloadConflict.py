from __future__ import annotations

import json
from pathlib import Path

import pytest

from video_forensics.native.decoder_matrix_report import build_report, frame_count_finding


def test_frame_count_divergence_is_high_severity() -> None:
    finding = frame_count_finding({"frame_counts": {"a": 192, "b": 236}})
    assert finding is not None
    assert finding["severity"] == "high"
    assert finding["observations"]["frame_count_range"] == 44


def test_build_report_prioritizes_frame_count_and_missing_refs(tmp_path: Path) -> None:
    matrix = tmp_path / "decoder_matrix.json"
    matrix.write_text(
        json.dumps(
            {
                "input_sha256": "abc",
                "frame_counts": {"single": 192, "multi": 236},
                "first_divergent_frame": 193,
                "missing_reference_pocs": {"multi": [0, 1], "single": []},
            }
        ),
        encoding="utf-8",
    )
    result = build_report(matrix, tmp_path / "report")
    assert [item["id"] for item in result["findings"][:2]] == [
        "DECODER_FRAME_COUNT_DIVERGENCE",
        "DECODER_MISSING_REFERENCE_DIAGNOSTICS",
    ]


def test_rejects_mismatched_perceptual_input(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.json"
    perceptual = tmp_path / "perceptual.json"
    matrix.write_text(json.dumps({"input_sha256": "one", "frame_counts": {}}))
    perceptual.write_text(json.dumps({"input_sha256": "two", "pairs": []}))
    with pytest.raises(ValueError, match="SHA-256"):
        build_report(matrix, tmp_path / "report", perceptual)

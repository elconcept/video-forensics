from __future__ import annotations

import hashlib
import json
from pathlib import Path

from video_forensics.native.hevc_migration_regression import evaluate


def test_all_reference_checks_must_pass(tmp_path: Path) -> None:
    source = tmp_path / "reference.h265"
    source.write_bytes(b"reference")
    digest = hashlib.sha256(b"reference").hexdigest()
    comparison = tmp_path / "comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "migration_acceptance": {"ffmpeg_control_passed": True},
                "semantic": {
                    "field_mismatch_count": 0,
                    "comparable_record_count": 4,
                    "legacy_semantic_agreement": True,
                    "rps_comparison_complete": True,
                },
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "main",
                        "source": source.name,
                        "source_sha256": digest,
                        "comparison": comparison.name,
                        "max_field_mismatches": 0,
                        "minimum_comparable_records": 4,
                        "require_legacy_agreement": True,
                        "require_complete_rps": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = evaluate(config, tmp_path / "result.json")
    assert result["passed"] is True
    assert result["legacy_removal_ready"] is True


def test_failed_control_blocks_legacy_removal(tmp_path: Path) -> None:
    source = tmp_path / "reference.h265"
    source.write_bytes(b"reference")
    comparison = tmp_path / "comparison.json"
    comparison.write_text(
        json.dumps(
            {
                "migration_acceptance": {"ffmpeg_control_passed": False},
                "semantic": {
                    "field_mismatch_count": 0,
                    "comparable_record_count": 1,
                    "legacy_semantic_agreement": True,
                },
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "main",
                        "source": source.name,
                        "comparison": comparison.name,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    result = evaluate(config, tmp_path / "result.json")
    assert result["passed"] is False
    assert result["legacy_removal_ready"] is False

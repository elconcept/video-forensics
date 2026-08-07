from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "finalize_hevc_parser_migration.py"
)
SPEC = importlib.util.spec_from_file_location(
    "finalize_hevc_parser_migration",
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {MODULE_PATH}")
finalize_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(finalize_module)
validate_gate = finalize_module.validate_gate


def gate(path: Path, *, passed: bool = True) -> None:
    ids = (
        "SOURCE_SHA256",
        "FFMPEG_CONTROL",
        "FIELD_MISMATCH_LIMIT",
        "COMPARABLE_RECORD_MINIMUM",
        "LEGACY_SEMANTIC_AGREEMENT",
        "RPS_COMPARISON_COMPLETE",
    )
    path.write_text(
        json.dumps(
            {
                "module": "hevc_migration_regression",
                "passed": passed,
                "legacy_removal_ready": passed,
                "cases": [
                    {
                        "passed": passed,
                        "checks": [
                            {"id": check_id, "passed": passed} for check_id in ids
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_accepts_fully_passing_gate(tmp_path: Path) -> None:
    path = tmp_path / "gate.json"
    gate(path)
    assert validate_gate(path)["legacy_removal_ready"] is True


def test_rejects_failed_gate(tmp_path: Path) -> None:
    path = tmp_path / "gate.json"
    gate(path, passed=False)
    with pytest.raises(ValueError, match="did not pass"):
        validate_gate(path)

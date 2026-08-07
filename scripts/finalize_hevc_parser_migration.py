from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

LEGACY_MODULES = (
    "src/video_forensics/tools/hevc_sps.py",
    "src/video_forensics/tools/hevc_pps.py",
    "src/video_forensics/tools/hevc_poc.py",
)
LEGACY_TEST_PATTERNS = (
    "test_hevc_sps*.py",
    "test_hevc_pps*.py",
    "test_hevc_poc*.py",
)


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def validate_gate(path: Path) -> dict[str, Any]:
    gate = read_object(path)
    if gate.get("module") != "hevc_migration_regression":
        raise ValueError("not a HEVC migration regression result")
    if gate.get("passed") is not True:
        raise ValueError("migration regression gate did not pass")
    if gate.get("legacy_removal_ready") is not True:
        raise ValueError("migration gate did not authorize legacy removal")
    cases = gate.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("migration gate has no reference cases")
    for case in cases:
        if not isinstance(case, dict) or case.get("passed") is not True:
            raise ValueError("not every reference case passed")
        checks = case.get("checks")
        if not isinstance(checks, list):
            raise TypeError("reference case has no checks list")
        passed = {
            str(check.get("id"))
            for check in checks
            if isinstance(check, dict) and check.get("passed") is True
        }
        required = {
            "SOURCE_SHA256",
            "FFMPEG_CONTROL",
            "FIELD_MISMATCH_LIMIT",
            "COMPARABLE_RECORD_MINIMUM",
            "LEGACY_SEMANTIC_AGREEMENT",
            "RPS_COMPARISON_COMPLETE",
        }
        missing = sorted(required - passed)
        if missing:
            raise ValueError("reference case lacks passing checks: " + ", ".join(missing))
    return gate


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def remove_legacy(repository: Path, gate_path: Path) -> dict[str, Any]:
    raise RuntimeError(
        "Legacy removal is blocked: hevc_bitstream, hevc_long_term_rps, "
        "hevc_short_term_rps, hevc_slice_address, hevc_slice_segments, and "
        "orphan_independent_run still depend on hevc_poc. Migrate those consumers first."
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="finalize-hevc-parser-migration")
    parser.add_argument("gate", type=Path)
    parser.add_argument("--repository", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        result = remove_legacy(args.repository, args.gate)
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

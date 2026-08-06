from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def validate_comparison(path: Path) -> dict[str, Any]:
    comparison = read_object(path)
    acceptance = comparison.get("migration_acceptance")
    semantic = comparison.get("semantic")
    if not isinstance(acceptance, dict):
        raise TypeError("comparison has no migration_acceptance object")
    if not isinstance(semantic, dict):
        raise TypeError("comparison has no semantic object")
    if not acceptance.get("ffmpeg_control_passed"):
        raise ValueError("FFmpeg control did not pass")
    if not acceptance.get("legacy_comparison_requested"):
        raise ValueError("comparison was produced without legacy backend")
    return comparison


def relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def enroll(
    config: Path,
    *,
    case_id: str,
    source: Path,
    comparison: Path,
    require_complete_rps: bool,
    minimum_comparable_records: int,
) -> dict[str, Any]:
    source = source.expanduser().resolve(strict=True)
    comparison = comparison.expanduser().resolve(strict=True)
    parsed = validate_comparison(comparison)
    semantic = parsed["semantic"]
    actual_records = int(semantic.get("comparable_record_count", 0))
    if actual_records < minimum_comparable_records:
        raise ValueError(
            f"comparison has only {actual_records} comparable records; "
            f"minimum is {minimum_comparable_records}"
        )
    if require_complete_rps and not semantic.get("rps_comparison_complete"):
        raise ValueError("comparison does not have complete RPS coverage")

    config = config.expanduser().resolve()
    config.parent.mkdir(parents=True, exist_ok=True)
    if config.exists():
        payload = read_object(config)
    else:
        payload = {"schema_version": 1, "cases": []}
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise TypeError("configuration cases must be a list")
    if any(isinstance(item, dict) and item.get("case_id") == case_id for item in cases):
        raise ValueError(f"case_id already exists: {case_id}")

    base = config.parent
    case = {
        "case_id": case_id,
        "source": relative_or_absolute(source, base),
        "source_sha256": sha256(source),
        "comparison": relative_or_absolute(comparison, base),
        "max_field_mismatches": 0,
        "minimum_comparable_records": minimum_comparable_records,
        "require_legacy_agreement": True,
        "require_complete_rps": require_complete_rps,
        "enrollment_evidence": {
            "actual_comparable_records": actual_records,
            "actual_field_mismatches": semantic.get("field_mismatch_count"),
            "actual_rps_comparison_complete": semantic.get(
                "rps_comparison_complete"
            ),
            "ffmpeg_control_passed": True,
            "legacy_comparison_requested": True,
        },
    }
    cases.append(case)
    payload["cases"] = cases
    config.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return case


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-hevc-reference-enroll")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--comparison", required=True, type=Path)
    parser.add_argument("--minimum-comparable-records", type=int, default=1)
    parser.add_argument("--allow-incomplete-rps", action="store_true")
    args = parser.parse_args()
    try:
        case = enroll(
            args.config,
            case_id=args.case_id,
            source=args.source,
            comparison=args.comparison,
            require_complete_rps=not args.allow_incomplete_rps,
            minimum_comparable_records=args.minimum_comparable_records,
        )
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(case, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

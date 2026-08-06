from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PARAMETER_SET_TYPES = {32: "vps", 33: "sps", 34: "pps"}
SLICE_TYPES = set(range(32))
FFMPEG_FIELD = re.compile(
    r"(?:^|\s)(?P<name>[A-Za-z_][A-Za-z0-9_\[\]]*)\s+"
    r"(?P<bits>[01]+)\s*=\s*(?P<value>-?\d+)\s*$"
)


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten(child, name))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.update(flatten(child, f"{prefix}[{index}]"))
    else:
        result[prefix] = value
    return result


def payload_object(nal: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    nal_type = nal.get("nal_unit_type")
    payload = nal.get("payload")
    if not isinstance(payload, dict):
        return None
    if nal_type in PARAMETER_SET_TYPES:
        name = PARAMETER_SET_TYPES[int(nal_type)]
        value = payload.get(name)
        return (name, value) if isinstance(value, dict) else None
    if nal_type in SLICE_TYPES:
        value = payload.get("slice_segment_layer") or payload.get("slice")
        return ("slice", value) if isinstance(value, dict) else None
    return None


def h265nal_records(primary: dict[str, Any]) -> list[dict[str, Any]]:
    nals = primary.get("nal_units")
    if not isinstance(nals, list):
        raise TypeError("primary result has no nal_units list")
    records: list[dict[str, Any]] = []
    for nal in nals:
        if not isinstance(nal, dict):
            continue
        parsed = payload_object(nal)
        if parsed is None:
            continue
        kind, value = parsed
        records.append(
            {
                "nal_number": nal.get("nal_number"),
                "nal_unit_type": nal.get("nal_unit_type"),
                "kind": kind,
                "fields": flatten(value),
            }
        )
    return records


def legacy_records(legacy: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = legacy.get("records")
    if isinstance(candidates, list):
        return [item for item in candidates if isinstance(item, dict)]
    records: list[dict[str, Any]] = []
    for key, kind in (("sps", "sps"), ("pps", "pps"), ("slices", "slice")):
        values = legacy.get(key)
        if not isinstance(values, list):
            continue
        for index, value in enumerate(values, start=1):
            if isinstance(value, dict):
                records.append(
                    {
                        "nal_number": value.get("nal_number", index),
                        "nal_unit_type": value.get("nal_unit_type"),
                        "kind": kind,
                        "fields": flatten(value.get("fields", value)),
                    }
                )
    return records


def parse_ffmpeg_trace(text: str) -> dict[str, list[int]]:
    fields: dict[str, list[int]] = {}
    for line in text.splitlines():
        match = FFMPEG_FIELD.search(line.strip())
        if match is None:
            continue
        fields.setdefault(match.group("name"), []).append(int(match.group("value")))
    return fields


def compare_fields(
    primary: list[dict[str, Any]], legacy: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for index, left in enumerate(primary):
        if index >= len(legacy):
            comparisons.append(
                {
                    "record_index": index,
                    "kind": left["kind"],
                    "status": "missing_legacy_record",
                }
            )
            continue
        right = legacy[index]
        left_fields = left.get("fields", {})
        right_fields = right.get("fields", {})
        shared = sorted(set(left_fields) & set(right_fields))
        mismatches = [
            {
                "field": field,
                "primary": left_fields[field],
                "legacy": right_fields[field],
            }
            for field in shared
            if left_fields[field] != right_fields[field]
        ]
        comparisons.append(
            {
                "record_index": index,
                "kind": left["kind"],
                "primary_nal_number": left.get("nal_number"),
                "legacy_nal_number": right.get("nal_number"),
                "shared_field_count": len(shared),
                "mismatch_count": len(mismatches),
                "mismatches": mismatches,
                "status": "match" if shared and not mismatches else "mismatch",
            }
        )
    return comparisons


def compare(
    primary: dict[str, Any],
    legacy: dict[str, Any] | None,
    ffmpeg_trace: str | None,
) -> dict[str, Any]:
    primary_items = h265nal_records(primary)
    legacy_items = legacy_records(legacy) if legacy is not None else []
    record_comparisons = (
        compare_fields(primary_items, legacy_items) if legacy is not None else []
    )
    ffmpeg_fields = parse_ffmpeg_trace(ffmpeg_trace or "")
    mismatch_count = sum(
        int(item.get("mismatch_count", 0)) for item in record_comparisons
    )
    comparable_count = sum(
        item.get("shared_field_count", 0) > 0 for item in record_comparisons
    )
    legacy_agreement = (
        legacy is not None
        and comparable_count > 0
        and mismatch_count == 0
        and len(primary_items) == len(legacy_items)
    )
    ffmpeg_control_available = bool(ffmpeg_fields)
    return {
        "schema_version": 1,
        "module": "hevc_semantic_compare",
        "primary_backend": "h265nal",
        "legacy_backend_role": "comparison_only",
        "control_backend": "ffmpeg_trace_headers",
        "primary_record_count": len(primary_items),
        "legacy_record_count": len(legacy_items),
        "comparable_record_count": comparable_count,
        "field_mismatch_count": mismatch_count,
        "legacy_semantic_agreement": legacy_agreement,
        "ffmpeg_control_available": ffmpeg_control_available,
        "authoritative_for_high_weight": ffmpeg_control_available,
        "records": record_comparisons,
        "ffmpeg_fields": ffmpeg_fields,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-hevc-semantic-compare")
    parser.add_argument("primary_json", type=Path)
    parser.add_argument("--legacy-json", type=Path)
    parser.add_argument("--ffmpeg-trace", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        primary = read_object(args.primary_json)
        legacy = read_object(args.legacy_json) if args.legacy_json else None
        trace = (
            args.ffmpeg_trace.read_text(encoding="utf-8", errors="replace")
            if args.ffmpeg_trace
            else None
        )
        result = compare(primary, legacy, trace)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

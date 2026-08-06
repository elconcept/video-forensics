from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from video_forensics.native.orphan_plan_review import verify_approved_plan


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def start_codes(data: bytes) -> list[tuple[int, int]]:
    starts: list[tuple[int, int]] = []
    index = 0
    while index <= len(data) - 3:
        if data[index : index + 4] == b"\x00\x00\x00\x01":
            starts.append((index, 4))
            index += 4
        elif data[index : index + 3] == b"\x00\x00\x01":
            starts.append((index, 3))
            index += 3
        else:
            index += 1
    return starts


def parse_nal_units(path: Path) -> list[dict[str, object]]:
    data = path.read_bytes()
    starts = start_codes(data)
    rows: list[dict[str, object]] = []
    for index, (offset, prefix_size) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(data)
        payload_offset = offset + prefix_size
        if end - payload_offset < 2:
            continue
        first = data[payload_offset]
        nal_type = (first >> 1) & 0x3F
        rows.append(
            {
                "nal_number": len(rows) + 1,
                "offset": offset,
                "end": end,
                "size_bytes": end - offset,
                "nal_unit_type": nal_type,
                "sha256": sha256_bytes(data[offset:end]),
                "bytes": data[offset:end],
            }
        )
    if not rows:
        raise ValueError(f"no Annex B NAL units found: {path}")
    return rows


def load_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"plan must be a JSON object: {path}")
    return payload


def select(rows: list[dict[str, object]], numbers: list[int], label: str) -> list[dict[str, object]]:
    lookup = {int(row["nal_number"]): row for row in rows}
    missing = [number for number in numbers if number not in lookup]
    if missing:
        raise ValueError(f"{label} references missing NAL numbers: {missing}")
    return [lookup[number] for number in numbers]


def validate_plan(rows: list[dict[str, object]], plan: dict[str, Any]) -> dict[str, object]:
    parameters = [int(value) for value in plan["parameter_nals"]]
    references = [int(value) for value in plan["reference_idr_nals"]]
    orphan_start = int(plan["orphan_start_nal"])
    orphan_end = int(plan["orphan_end_nal"])
    if orphan_start > orphan_end:
        raise ValueError("orphan_start_nal must not exceed orphan_end_nal")

    parameter_rows = select(rows, parameters, "parameter_nals")
    reference_rows = select(rows, references, "reference_idr_nals")
    orphan_rows = select(rows, list(range(orphan_start, orphan_end + 1)), "orphan range")

    invalid_parameters = [
        int(row["nal_number"])
        for row in parameter_rows
        if int(row["nal_unit_type"]) not in {32, 33, 34}
    ]
    if invalid_parameters:
        raise ValueError(f"parameter_nals contain non-VPS/SPS/PPS NALs: {invalid_parameters}")

    invalid_references = [
        int(row["nal_number"])
        for row in reference_rows
        if int(row["nal_unit_type"]) not in {19, 20}
    ]
    if invalid_references:
        raise ValueError(f"reference_idr_nals contain non-IDR NALs: {invalid_references}")

    invalid_orphans = [
        int(row["nal_number"])
        for row in orphan_rows
        if int(row["nal_unit_type"]) >= 32
    ]
    if invalid_orphans:
        raise ValueError(f"orphan range contains non-VCL NALs: {invalid_orphans}")

    return {
        "parameter_rows": parameter_rows,
        "reference_rows": reference_rows,
        "orphan_rows": orphan_rows,
        "orphan_start": orphan_start,
        "orphan_end": orphan_end,
    }


def build(
    annex_b: Path,
    plan_path: Path,
    output: Path,
) -> dict[str, object]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    plan_path = plan_path.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)

    rows = parse_nal_units(annex_b)
    plan = load_plan(plan_path)
    verify_approved_plan(annex_b, plan)
    validated = validate_plan(rows, plan)
    parameter_rows = validated["parameter_rows"]
    reference_rows = validated["reference_rows"]
    orphan_rows = validated["orphan_rows"]
    prefix = b"".join(bytes(row["bytes"]) for row in parameter_rows)
    orphan = b"".join(bytes(row["bytes"]) for row in orphan_rows)

    variants: list[dict[str, object]] = []
    for reference in reference_rows:
        reference_number = int(reference["nal_number"])
        content = prefix + bytes(reference["bytes"]) + orphan
        filename = f"orphan_ref_nal_{reference_number:06d}.h265"
        target = output / filename
        target.write_bytes(content)
        variants.append(
            {
                "reference_nal_number": reference_number,
                "reference_nal_sha256": reference["sha256"],
                "file": filename,
                "size_bytes": len(content),
                "sha256": sha256_bytes(content),
            }
        )

    index_rows = [
        {
            "nal_number": int(row["nal_number"]),
            "nal_unit_type": int(row["nal_unit_type"]),
            "offset": int(row["offset"]),
            "size_bytes": int(row["size_bytes"]),
            "sha256": str(row["sha256"]),
            "role": (
                "parameter"
                if row in parameter_rows
                else "reference"
                if row in reference_rows
                else "orphan"
                if row in orphan_rows
                else "unused"
            ),
        }
        for row in rows
    ]
    with (output / "nal_index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(index_rows[0]))
        writer.writeheader()
        writer.writerows(index_rows)

    manifest: dict[str, object] = {
        "schema_version": 1,
        "module": "orphan_stream_builder",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "path": str(annex_b),
            "size_bytes": annex_b.stat().st_size,
            "sha256": sha256_bytes(annex_b.read_bytes()),
        },
        "plan": plan,
        "validated": {
            "parameter_nals": [int(row["nal_number"]) for row in parameter_rows],
            "reference_idr_nals": [int(row["nal_number"]) for row in reference_rows],
            "orphan_start_nal": validated["orphan_start"],
            "orphan_end_nal": validated["orphan_end"],
            "orphan_nal_count": len(orphan_rows),
        },
        "variants": variants,
        "interpretation_boundary": (
            "The builder performs byte-exact NAL concatenation from an analyst-supplied plan. "
            "It does not infer the orphan boundary or prove that a selected IDR is the missing reference."
        ),
    }
    (output / "orphan_streams.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-build-orphan-streams")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.annex_b, args.plan, args.output)
    except (FileNotFoundError, FileExistsError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"variant_count": len(result["variants"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

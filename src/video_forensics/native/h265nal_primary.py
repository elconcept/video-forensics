from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

IRAP_TYPES = set(range(16, 24))
IDR_TYPES = {19, 20}


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def nested(container: Any, *keys: str) -> Any:
    current = container
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_int(mapping: Any, names: tuple[str, ...]) -> int | None:
    if not isinstance(mapping, dict):
        return None
    for name in names:
        value = mapping.get(name)
        if isinstance(value, int):
            return value
    return None


def nal_payload(unit: dict[str, Any]) -> dict[str, Any]:
    payload = unit.get("payload")
    if isinstance(payload, dict):
        return payload
    return {}


def syntax_object(unit: dict[str, Any], name: str) -> dict[str, Any] | None:
    payload = nal_payload(unit)
    value = payload.get(name)
    if isinstance(value, dict):
        return value
    raw = unit.get("raw")
    if isinstance(raw, dict):
        value = raw.get(name)
        if isinstance(value, dict):
            return value
    return None


def slice_header(unit: dict[str, Any]) -> dict[str, Any] | None:
    payload = nal_payload(unit)
    value = nested(payload, "slice_segment_layer", "slice_segment_header")
    return value if isinstance(value, dict) else None


def derive_poc(
    poc_lsb: int,
    previous_lsb: int,
    previous_msb: int,
    log2_max_poc_lsb: int,
) -> tuple[int, int]:
    maximum = 1 << log2_max_poc_lsb
    if poc_lsb < previous_lsb and previous_lsb - poc_lsb >= maximum // 2:
        poc_msb = previous_msb + maximum
    elif poc_lsb > previous_lsb and poc_lsb - previous_lsb > maximum // 2:
        poc_msb = previous_msb - maximum
    else:
        poc_msb = previous_msb
    return poc_msb + poc_lsb, poc_msb


def register_version(
    versions: dict[str, list[dict[str, Any]]],
    identifier: int,
    unit: dict[str, Any],
    syntax: dict[str, Any],
) -> dict[str, Any]:
    key = str(identifier)
    history = versions.setdefault(key, [])
    digest = canonical_hash(syntax)
    if history and history[-1]["syntax_sha256"] == digest:
        history[-1]["last_nal_number"] = unit["nal_number"]
        return history[-1]
    version = {
        "id": identifier,
        "version": len(history) + 1,
        "first_nal_number": unit["nal_number"],
        "last_nal_number": unit["nal_number"],
        "offset": unit.get("offset"),
        "length": unit.get("length"),
        "syntax_sha256": digest,
        "syntax": syntax,
    }
    history.append(version)
    return version


def analyze(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != 1 or document.get("module") != "h265nal_adapter":
        raise ValueError("unsupported h265nal adapter document")
    units = document.get("nal_units")
    if not isinstance(units, list):
        raise TypeError("h265nal document has no nal_units list")

    versions: dict[str, dict[str, list[dict[str, Any]]]] = {
        "vps": {},
        "sps": {},
        "pps": {},
    }
    active_sps: dict[int, dict[str, Any]] = {}
    active_pps: dict[int, dict[str, Any]] = {}
    pictures: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    previous_lsb = 0
    previous_msb = 0
    previous_poc: int | None = None

    for unit in units:
        if not isinstance(unit, dict):
            errors.append({"error": "NAL record is not an object"})
            continue
        header = unit.get("header")
        nal_type = first_int(header, ("nal_unit_type",))
        nal_number = unit.get("nal_number")
        if nal_type is None or not isinstance(nal_number, int):
            errors.append({"nal_number": nal_number, "error": "missing NAL type or number"})
            continue

        if nal_type == 32:
            value = syntax_object(unit, "vps")
            identifier = first_int(value, ("vps_video_parameter_set_id", "video_parameter_set_id"))
            if value is None or identifier is None:
                errors.append({"nal_number": nal_number, "error": "VPS syntax or ID missing"})
            else:
                register_version(versions["vps"], identifier, unit, value)
            continue
        if nal_type == 33:
            value = syntax_object(unit, "sps")
            identifier = first_int(value, ("sps_seq_parameter_set_id", "seq_parameter_set_id"))
            if value is None or identifier is None:
                errors.append({"nal_number": nal_number, "error": "SPS syntax or ID missing"})
            else:
                active_sps[identifier] = register_version(
                    versions["sps"], identifier, unit, value
                )
            continue
        if nal_type == 34:
            value = syntax_object(unit, "pps")
            identifier = first_int(value, ("pps_pic_parameter_set_id", "pic_parameter_set_id"))
            sps_id = first_int(value, ("pps_seq_parameter_set_id", "seq_parameter_set_id"))
            if value is None or identifier is None or sps_id is None:
                errors.append({"nal_number": nal_number, "error": "PPS syntax or IDs missing"})
            else:
                version = register_version(versions["pps"], identifier, unit, value)
                version["sps_id"] = sps_id
                active_pps[identifier] = version
            continue
        if not 0 <= nal_type < 32:
            continue

        slice_value = slice_header(unit)
        if slice_value is None:
            errors.append({"nal_number": nal_number, "error": "VCL NAL has no parsed slice header"})
            continue
        first_slice = first_int(slice_value, ("first_slice_segment_in_pic_flag",))
        if first_slice != 1:
            continue
        pps_id = first_int(slice_value, ("slice_pic_parameter_set_id",))
        if pps_id is None or pps_id not in active_pps:
            errors.append({"nal_number": nal_number, "error": f"active PPS {pps_id} unavailable"})
            continue
        pps_version = active_pps[pps_id]
        sps_id = int(pps_version["sps_id"])
        if sps_id not in active_sps:
            errors.append({"nal_number": nal_number, "error": f"active SPS {sps_id} unavailable"})
            continue
        sps_version = active_sps[sps_id]
        sps = sps_version["syntax"]
        log2_minus4 = first_int(
            sps,
            ("log2_max_pic_order_cnt_lsb_minus4", "log2_max_pic_order_cnt_lsb_minus4_value"),
        )
        if log2_minus4 is None:
            errors.append({"nal_number": nal_number, "error": "SPS POC width unavailable"})
            continue
        log2_max_poc_lsb = log2_minus4 + 4
        if nal_type in IDR_TYPES:
            poc_lsb = 0
            poc_msb = 0
            poc = 0
            previous_lsb = 0
            previous_msb = 0
        else:
            poc_lsb = first_int(slice_value, ("slice_pic_order_cnt_lsb",))
            if poc_lsb is None:
                errors.append({"nal_number": nal_number, "error": "slice POC LSB unavailable"})
                continue
            poc, poc_msb = derive_poc(
                poc_lsb, previous_lsb, previous_msb, log2_max_poc_lsb
            )
            previous_lsb = poc_lsb
            previous_msb = poc_msb
        picture = {
            "picture_number": len(pictures) + 1,
            "nal_number": nal_number,
            "offset": unit.get("offset"),
            "length": unit.get("length"),
            "nal_unit_type": nal_type,
            "is_irap": nal_type in IRAP_TYPES,
            "pps_id": pps_id,
            "pps_version": pps_version["version"],
            "sps_id": sps_id,
            "sps_version": sps_version["version"],
            "slice_type": first_int(slice_value, ("slice_type",)),
            "slice_segment_address": first_int(slice_value, ("slice_segment_address",)),
            "poc_lsb": poc_lsb,
            "poc_msb": poc_msb,
            "poc": poc,
            "short_term_ref_pic_set_sps_flag": first_int(
                slice_value, ("short_term_ref_pic_set_sps_flag",)
            ),
            "slice_header": slice_value,
        }
        if previous_poc is not None and poc < previous_poc and nal_type not in IRAP_TYPES:
            findings.append(
                {
                    "id": "HEVC_POC_REGRESSION_WITHOUT_IRAP",
                    "severity": "high",
                    "description": "Picture Order Count decreased at a non-IRAP picture.",
                    "evidence_refs": [f"hevc_syntax/pictures.csv#picture-{picture['picture_number']}"],
                    "requires_reference": False,
                    "host_profile": None,
                    "observations": {
                        "previous_poc": previous_poc,
                        "current_poc": poc,
                        "nal_number": nal_number,
                        "offset": unit.get("offset"),
                        "pps_id": pps_id,
                        "pps_version": pps_version["version"],
                        "sps_id": sps_id,
                        "sps_version": sps_version["version"],
                    },
                }
            )
        pictures.append(picture)
        previous_poc = poc

    return {
        "schema_version": 1,
        "module": "h265nal_primary",
        "source": document.get("source"),
        "tool": document.get("tool"),
        "parameter_versions": versions,
        "picture_count": len(pictures),
        "pictures": pictures,
        "parse_error_count": len(errors),
        "parse_errors": errors,
        "finding_count": len(findings),
        "findings": findings,
        "automatic_orphan_plan_allowed": not errors,
        "interpretation_boundary": (
            "POC and active parameter-set assignment are derived from h265nal syntax output. "
            "Any parse error blocks automatic orphan-plan generation."
        ),
    }


def compare_legacy(primary: dict[str, Any], legacy: dict[str, Any]) -> dict[str, Any]:
    legacy_pictures = legacy.get("pictures")
    if not isinstance(legacy_pictures, list):
        raise TypeError("legacy document has no pictures list")
    primary_by_nal = {int(row["nal_number"]): row for row in primary["pictures"]}
    legacy_by_nal = {int(row["nal_number"]): row for row in legacy_pictures}
    all_nals = sorted(set(primary_by_nal) | set(legacy_by_nal))
    mismatches: list[dict[str, Any]] = []
    for nal_number in all_nals:
        left = primary_by_nal.get(nal_number)
        right = legacy_by_nal.get(nal_number)
        if left is None or right is None:
            mismatches.append(
                {"nal_number": nal_number, "primary": left, "legacy": right, "reason": "presence"}
            )
        elif left.get("poc") != right.get("poc"):
            mismatches.append(
                {
                    "nal_number": nal_number,
                    "primary_poc": left.get("poc"),
                    "legacy_poc": right.get("poc"),
                    "reason": "poc",
                }
            )
    return {
        "primary_picture_count": len(primary_by_nal),
        "legacy_picture_count": len(legacy_by_nal),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "status": "matched" if not mismatches else "mismatch",
    }


def write_outputs(result: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    (output / "hevc_syntax.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "parameter_versions.json").write_text(
        json.dumps(result["parameter_versions"], ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    columns = [
        "picture_number",
        "nal_number",
        "offset",
        "length",
        "nal_unit_type",
        "is_irap",
        "pps_id",
        "pps_version",
        "sps_id",
        "sps_version",
        "slice_type",
        "slice_segment_address",
        "poc_lsb",
        "poc_msb",
        "poc",
    ]
    with (output / "pictures.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in result["pictures"]:
            writer.writerow({key: row.get(key) for key in columns})


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-h265nal-primary")
    parser.add_argument("h265nal_json", type=Path)
    parser.add_argument("--legacy-poc-json", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = analyze(load_object(args.h265nal_json.expanduser().resolve(strict=True)))
        if args.legacy_poc_json is not None:
            comparison = compare_legacy(
                result,
                load_object(args.legacy_poc_json.expanduser().resolve(strict=True)),
            )
            result["legacy_comparison"] = comparison
            if comparison["status"] != "matched":
                result["automatic_orphan_plan_allowed"] = False
        write_outputs(result, args.output.expanduser().resolve())
    except (FileNotFoundError, FileExistsError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "picture_count": result["picture_count"],
                "parse_error_count": result["parse_error_count"],
                "automatic_orphan_plan_allowed": result["automatic_orphan_plan_allowed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

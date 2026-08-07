from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from video_forensics.tools.hevc_bitstream import parse_annex_b
from video_forensics.tools.hevc_poc import analyze_poc
from video_forensics.tools.hevc_pps import parse_pps_complete, pps_to_dict
from video_forensics.tools.hevc_sps import parse_sps_complete, sps_to_dict


def nal_type(row: dict[str, Any]) -> int:
    for key in ("nal_unit_type", "nal_type", "type"):
        if key in row:
            return int(row[key])
    raise KeyError("NAL row has no type field")


def nal_payload(row: dict[str, Any]) -> bytes:
    for key in ("payload", "nal_payload", "bytes", "data"):
        value = row.get(key)
        if isinstance(value, bytes):
            return value
        if isinstance(value, bytearray):
            return bytes(value)
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return bytes(value)
    raise TypeError("NAL row has no byte payload")


def export_legacy(annex_b: Path, output: Path) -> dict[str, Any]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    rows = parse_annex_b(annex_b)
    if not rows:
        raise ValueError("legacy Annex B parser returned no NAL units")
    nals: list[dict[str, Any]] = []
    sps: list[dict[str, Any]] = []
    pps: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for number, original in enumerate(rows, start=1):
        row = dict(original)
        kind = nal_type(row)
        payload = nal_payload(row)
        nals.append({"nal_number": number, "nal_unit_type": kind})
        try:
            if kind == 33:
                sps.append({"nal_number": number, "nal_unit_type": kind, "fields": sps_to_dict(parse_sps_complete(payload))})
            elif kind == 34:
                pps.append({"nal_number": number, "nal_unit_type": kind, "fields": pps_to_dict(parse_pps_complete(payload))})
        except (KeyError, TypeError, ValueError) as exc:
            errors.append({"nal_number": number, "nal_unit_type": kind, "error": str(exc)})
    poc = analyze_poc(rows)
    slices: list[dict[str, Any]] = []
    if isinstance(poc, dict):
        for key in ("pictures", "slices", "records"):
            values = poc.get(key)
            if isinstance(values, list):
                slices = [value for value in values if isinstance(value, dict)]
                break
    sps_by_id = {
        int(item["fields"]["sps_id"]): item["fields"]
        for item in sps
        if isinstance(item.get("fields"), dict)
        and item["fields"].get("sps_id") is not None
    }
    pps_to_sps = {
        int(item["fields"]["pps_id"]): int(item["fields"]["sps_id"])
        for item in pps
        if isinstance(item.get("fields"), dict)
        and item["fields"].get("pps_id") is not None
        and item["fields"].get("sps_id") is not None
    }
    enriched_slices: list[dict[str, Any]] = []
    for item in slices:
        enriched = dict(item)
        pps_id = enriched.get("pps_id")
        if isinstance(pps_id, int) and pps_id in pps_to_sps:
            source_sps = sps_by_id.get(pps_to_sps[pps_id], {})
            rps_sets = source_sps.get("short_term_ref_pic_sets", [])
            if isinstance(rps_sets, list) and rps_sets:
                selected = rps_sets[0]
                if isinstance(selected, dict):
                    enriched["short_term_ref_pic_set_sps_flag"] = 1
                    for key in ("num_negative_pics", "num_positive_pics"):
                        if key in selected:
                            enriched[key] = selected[key]
        enriched_slices.append(enriched)
    slices = enriched_slices

    records = [
        *({"nal_number": item["nal_number"], "nal_unit_type": item["nal_unit_type"], "kind": "sps", "fields": item["fields"]} for item in sps),
        *({"nal_number": item["nal_number"], "nal_unit_type": item["nal_unit_type"], "kind": "pps", "fields": item["fields"]} for item in pps),
        *({"nal_number": item.get("nal_number", index), "nal_unit_type": item.get("nal_unit_type"), "kind": "slice", "fields": item} for index, item in enumerate(slices, start=1)),
    ]
    result = {"schema_version": 1, "module": "hevc_legacy_export", "backend": "legacy", "role": "comparison_only", "input": str(annex_b), "nal_count": len(nals), "nal_units": nals, "sps": sps, "pps": pps, "slices": slices, "records": records, "poc": poc, "parse_errors": errors, "parse_error_count": len(errors)}
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-hevc-legacy-export")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = export_legacy(args.annex_b, args.output)
    except (FileNotFoundError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"nal_count": result["nal_count"], "parse_error_count": result["parse_error_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

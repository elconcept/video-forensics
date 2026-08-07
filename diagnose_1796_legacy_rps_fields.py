from __future__ import annotations

import json
from pathlib import Path
from typing import Any

root = Path("work/results/1796")
runs = sorted(path for path in root.iterdir() if path.is_dir() and path.name[:1].isdigit())
if not runs:
    raise SystemExit(f"Brak przebiegów w {root}")
run = runs[-1]
base = run / "hevc_parser_migration"
legacy = json.loads((base / "legacy_comparison.json").read_text(encoding="utf-8"))
primary = json.loads(
    (base / "reference_comparison/authority/h265nal_normalized.json").read_text(
        encoding="utf-8"
    )
)


def find_rps(value: Any, path: str = "") -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            if any(token in key.lower() for token in ("rps", "ref_pic", "negative_pics", "positive_pics")):
                found.append({"path": child_path, "value": child})
            found.extend(find_rps(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_rps(child, f"{path}[{index}]"))
    return found

legacy_sps = legacy.get("sps", [])
legacy_poc_sps = legacy.get("poc", {}).get("sps", {}) if isinstance(legacy.get("poc"), dict) else {}
primary_sps = [
    row
    for row in primary.get("nal_units", [])
    if isinstance(row, dict) and row.get("nal_unit_type") == 33
]
primary_slices = [
    row
    for row in primary.get("nal_units", [])
    if isinstance(row, dict)
    and isinstance(row.get("nal_unit_type"), int)
    and row["nal_unit_type"] < 32
]
report = {
    "run": str(run),
    "legacy_sps_count": len(legacy_sps),
    "legacy_sps_rps_paths": find_rps(legacy_sps),
    "legacy_poc_sps": legacy_poc_sps,
    "legacy_poc_sps_rps_paths": find_rps(legacy_poc_sps),
    "primary_sps_rps_paths": find_rps(primary_sps),
    "primary_slice_rps_paths_first_20": find_rps(primary_slices[:20]),
}
output = base / "legacy_rps_field_diagnosis.json"
output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))

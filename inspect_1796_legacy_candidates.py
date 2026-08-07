from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path("work/results/1796")


def shape(value: Any) -> str:
    if isinstance(value, dict):
        return "object{" + ",".join(sorted(map(str, value.keys()))[:30]) + "}"
    if isinstance(value, list):
        first = shape(value[0]) if value else "empty"
        return f"list[{len(value)}]({first})"
    return type(value).__name__

runs = sorted(path for path in ROOT.iterdir() if path.is_dir() and path.name[:1].isdigit())
if not runs:
    raise SystemExit(f"Brak przebiegów w {ROOT}")
run = runs[-1]
rows = []
for path in sorted(run.rglob("*.json")):
    if "hevc_parser_migration" in path.parts:
        continue
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        rows.append({"path": str(path.relative_to(run)), "error": str(exc)})
        continue
    rows.append(
        {
            "path": str(path.relative_to(run)),
            "shape": shape(payload),
            "module": payload.get("module") if isinstance(payload, dict) else None,
            "backend": payload.get("backend") if isinstance(payload, dict) else None,
        }
    )
output = run / "legacy_schema_inventory.json"
output.write_text(json.dumps({"run": str(run), "files": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(output)

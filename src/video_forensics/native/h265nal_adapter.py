from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
INTEGER = re.compile(r"^-?\d+$")
HEX_INTEGER = re.compile(r"^0x[0-9a-fA-F]+$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def find_h265nal(explicit: str | None) -> Path:
    candidates = [explicit] if explicit else ["h265nal", "tools/h265nal"]
    for candidate in candidates:
        if not candidate:
            continue
        located = shutil.which(candidate)
        if located:
            return Path(located).resolve(strict=True)
        path = Path(candidate).expanduser()
        if path.is_file():
            return path.resolve(strict=True)
    raise FileNotFoundError(
        "cannot find h265nal; pass --h265nal or run scripts/build_h265nal.py"
    )


def scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return None
    if HEX_INTEGER.fullmatch(value):
        return int(value, 16)
    if INTEGER.fullmatch(value):
        return int(value)
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def add_value(target: dict[str, Any], key: str, value: Any) -> None:
    if key not in target:
        target[key] = value
        return
    current = target[key]
    if not isinstance(current, list):
        target[key] = [current]
    target[key].append(value)


def parse_brace_dump(text: str) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("h265nal:"):
            continue
        if line == "}":
            if not stack:
                raise ValueError(f"unexpected closing brace at line {line_number}")
            stack.pop()
            continue
        empty_match = re.fullmatch(r"([^{}:]+)\s*\{\s*\}", line)
        if empty_match:
            if not stack:
                raise ValueError(f"empty object without parent at line {line_number}")
            add_value(stack[-1], empty_match.group(1).strip(), {})
            continue
        object_match = re.fullmatch(r"([^{}:]+)\s*\{", line)
        if object_match:
            key = object_match.group(1).strip()
            item: dict[str, Any] = {}
            if not stack:
                root = {key: item}
                roots.append(root)
            else:
                add_value(stack[-1], key, item)
            stack.append(item)
            continue
        array_match = re.fullmatch(r"([^{}:]+)\s*\{\s*(.*?)\s*\}", line)
        if array_match:
            if not stack:
                raise ValueError(f"array without parent at line {line_number}")
            values = [scalar(value) for value in array_match.group(2).split()]
            add_value(stack[-1], array_match.group(1).strip(), values)
            continue
        field_match = re.fullmatch(r"([^:]+):\s*(.*)", line)
        if field_match:
            if not stack:
                raise ValueError(f"field without parent at line {line_number}")
            add_value(
                stack[-1],
                field_match.group(1).strip(),
                scalar(field_match.group(2)),
            )
            continue
        raise ValueError(f"unrecognized h265nal output at line {line_number}: {line}")
    if stack:
        raise ValueError("unterminated object in h265nal output")
    return roots


def normalize_nal(root: dict[str, Any], number: int) -> dict[str, Any]:
    payload = root.get("nal_unit")
    if not isinstance(payload, dict):
        raise ValueError(f"root {number} is not a nal_unit")
    header = payload.get("nal_unit_header")
    if not isinstance(header, dict):
        raise ValueError(f"NAL {number} has no nal_unit_header")
    return {
        "nal_number": number,
        "offset": payload.get("offset"),
        "length": payload.get("length"),
        "header": header,
        "payload": payload.get("nal_unit_payload", {}),
        "raw": payload,
    }


def command(binary: Path, annex_b: Path) -> list[str]:
    return [
        str(binary),
        "-i",
        str(annex_b),
        "--no-as-one-line",
        "--add-length",
        "--add-offset",
    ]


def run(
    annex_b: Path,
    output: Path,
    *,
    binary: Path,
    timeout: int,
) -> dict[str, Any]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise FileExistsError(f"output already exists and is not empty: {output}")
    else:
        output.mkdir(parents=True, exist_ok=False)
    argv = command(binary, annex_b)
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    (output / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(
            f"h265nal failed with return code {completed.returncode}; see stderr.txt"
        )
    roots = parse_brace_dump(completed.stdout)
    units = [normalize_nal(root, index) for index, root in enumerate(roots, start=1)]
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "module": "h265nal_adapter",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "path": str(annex_b),
            "size_bytes": annex_b.stat().st_size,
            "sha256": sha256(annex_b),
        },
        "tool": {
            "path": str(binary),
            "upstream": "chemag/h265nal",
        },
        "command": argv,
        "returncode": completed.returncode,
        "nal_count": len(units),
        "nal_units": units,
        "interpretation_boundary": (
            "The JSON is a normalized representation of h265nal CLI output. "
            "Bitstream findings must preserve the raw dump and tool identity."
        ),
    }
    (output / "h265nal.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-h265nal")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--h265nal")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = run(
            args.annex_b,
            args.output,
            binary=find_h265nal(args.h265nal),
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"nal_count": result["nal_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

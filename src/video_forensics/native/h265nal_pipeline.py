from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from video_forensics.native.h265nal_adapter import find_h265nal
from video_forensics.native.h265nal_adapter import run as run_adapter
from video_forensics.native.h265nal_primary import (
    analyze,
    compare_legacy,
    load_object,
    write_outputs,
)


def ensure_h265nal(explicit: str | None, python: str) -> Path:
    try:
        return find_h265nal(explicit)
    except FileNotFoundError:
        if explicit:
            raise
    builder = Path("scripts/build_h265nal.py").resolve()
    if not builder.is_file():
        raise FileNotFoundError(
            "h265nal is unavailable and scripts/build_h265nal.py was not found"
        )
    subprocess.run([python, str(builder)], check=True)
    return find_h265nal(None)


def run_pipeline(
    annex_b: Path,
    output: Path,
    *,
    h265nal: str | None,
    python: str,
    legacy_json: Path | None,
    timeout: int,
) -> dict[str, Any]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    binary = ensure_h265nal(h265nal, python)
    with tempfile.TemporaryDirectory(prefix="h265nal-adapter-") as temporary:
        adapter_root = Path(temporary)
        adapter = run_adapter(
            annex_b,
            adapter_root,
            binary=binary,
            timeout=timeout,
        )
        primary = analyze(adapter)
        if legacy_json is not None:
            comparison = compare_legacy(
                primary,
                load_object(legacy_json.expanduser().resolve(strict=True)),
            )
            primary["legacy_comparison"] = comparison
            if comparison["status"] != "matched":
                primary["automatic_orphan_plan_allowed"] = False
        raw_root = output / "h265nal_raw"
        raw_root.mkdir()
        for name in ("stdout.txt", "stderr.txt", "h265nal.json"):
            shutil.copy2(adapter_root / name, raw_root / name)
    write_outputs(primary, output / "primary")
    result = {
        "schema_version": 1,
        "module": "h265nal_pipeline",
        "status": "completed",
        "source": primary.get("source"),
        "tool": primary.get("tool"),
        "picture_count": primary["picture_count"],
        "parse_error_count": primary["parse_error_count"],
        "finding_count": primary["finding_count"],
        "automatic_orphan_plan_allowed": primary["automatic_orphan_plan_allowed"],
        "legacy_comparison": primary.get("legacy_comparison"),
        "outputs": {
            "raw": "h265nal_raw/h265nal.json",
            "syntax": "primary/hevc_syntax.json",
            "pictures": "primary/pictures.csv",
            "parameter_versions": "primary/parameter_versions.json",
        },
    }
    (output / "h265nal_pipeline.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-hevc-syntax")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--h265nal")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--legacy-poc-json", type=Path)
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = run_pipeline(
            args.annex_b,
            args.output,
            h265nal=args.h265nal,
            python=args.python,
            legacy_json=args.legacy_poc_json,
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

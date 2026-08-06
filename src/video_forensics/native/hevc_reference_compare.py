from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from video_forensics.native.hevc_parser_authority import run as run_authority
from video_forensics.native.hevc_semantic_compare import compare


def run_trace(ffmpeg: Path, annex_b: Path, output: Path, timeout: int) -> dict[str, Any]:
    argv = [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "info",
        "-f",
        "hevc",
        "-i",
        str(annex_b),
        "-map",
        "0:v:0",
        "-c:v",
        "copy",
        "-bsf:v",
        "trace_headers",
        "-f",
        "null",
        "-",
    ]
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    output.write_text(completed.stderr, encoding="utf-8")
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "success": completed.returncode == 0,
        "trace": str(output),
    }


def run(
    annex_b: Path,
    output: Path,
    *,
    repository: Path,
    ffmpeg: Path,
    ffprobe: str | None,
    wrapper: str | None,
    h265nal: str | None,
    legacy_json: Path | None,
    timeout: int,
) -> dict[str, Any]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    authority = run_authority(
        annex_b,
        output / "authority",
        repository=repository,
        wrapper=wrapper,
        h265nal=h265nal,
        ffprobe=ffprobe,
        legacy_json=legacy_json,
        timeout=timeout,
    )
    trace = run_trace(ffmpeg, annex_b, output / "ffmpeg_trace_headers.txt", timeout)
    legacy = None
    if legacy_json is not None:
        value = json.loads(legacy_json.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError("legacy JSON must be an object")
        legacy = value
    semantic = compare(
        authority["primary"],
        legacy,
        (output / "ffmpeg_trace_headers.txt").read_text(
            encoding="utf-8", errors="replace"
        ),
    )
    result = {
        "schema_version": 1,
        "module": "hevc_reference_compare",
        "input": str(annex_b),
        "primary_backend": "h265nal",
        "legacy_backend_role": "comparison_only",
        "control_backend": "ffmpeg_trace_headers",
        "trace": trace,
        "semantic": semantic,
        "migration_acceptance": {
            "ffmpeg_control_passed": bool(trace["success"]),
            "legacy_comparison_requested": legacy_json is not None,
            "legacy_semantic_agreement": semantic["legacy_semantic_agreement"],
            "ready_for_legacy_removal": bool(trace["success"])
            and legacy_json is not None
            and bool(semantic["legacy_semantic_agreement"]),
        },
    }
    (output / "reference_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-hevc-reference-compare")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--ffmpeg", required=True, type=Path)
    parser.add_argument("--ffprobe")
    parser.add_argument("--wrapper")
    parser.add_argument("--h265nal")
    parser.add_argument("--legacy-json", type=Path)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    try:
        result = run(
            args.annex_b,
            args.output,
            repository=args.repository,
            ffmpeg=args.ffmpeg.expanduser().resolve(strict=True),
            ffprobe=args.ffprobe,
            wrapper=args.wrapper,
            h265nal=args.h265nal,
            legacy_json=args.legacy_json,
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result["migration_acceptance"], indent=2))
    return 0 if result["migration_acceptance"]["ffmpeg_control_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

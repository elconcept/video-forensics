from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from video_forensics.native.hevc_legacy_export import export_legacy
from video_forensics.native.hevc_parser_authority import run as run_authority
from video_forensics.native.hevc_reference_compare import run as run_reference_compare


def resolve_binary(explicit: str | None, name: str) -> Path:
    candidate = explicit or shutil.which(name)
    if not candidate:
        raise FileNotFoundError(f"cannot find {name}; pass --{name}")
    return Path(candidate).expanduser().resolve(strict=True)


def execute_json(argv: list[str], timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "command failed")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise TypeError("command output must be a JSON object")
    return value


def codec_name(video: Path, ffprobe: Path, timeout: int) -> str:
    value = execute_json(
        [
            str(ffprobe),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name",
            "-of",
            "json",
            str(video),
        ],
        timeout,
    )
    streams = value.get("streams")
    if not isinstance(streams, list) or not streams:
        raise ValueError("input contains no primary video stream")
    stream = streams[0]
    if not isinstance(stream, dict) or not stream.get("codec_name"):
        raise ValueError("ffprobe did not report the video codec")
    return str(stream["codec_name"])


def extract_annex_b(
    video: Path,
    output: Path,
    ffmpeg: Path,
    timeout: int,
) -> dict[str, object]:
    argv = [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-c:v",
        "copy",
        "-bsf:v",
        "hevc_mp4toannexb",
        "-f",
        "hevc",
        str(output),
    ]
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0 or not output.is_file():
        raise RuntimeError(completed.stderr.strip() or "HEVC Annex B extraction failed")
    return {"argv": argv, "stderr": completed.stderr, "size_bytes": output.stat().st_size}


def run_stage(
    video: Path,
    output: Path,
    *,
    repository: Path,
    ffmpeg_path: str | None,
    ffprobe_path: str | None,
    wrapper: str | None,
    h265nal: str | None,
    legacy_json: Path | None,
    timeout: int,
) -> dict[str, object]:
    video = video.expanduser().resolve(strict=True)
    repository = repository.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    ffmpeg = resolve_binary(ffmpeg_path, "ffmpeg")
    ffprobe = resolve_binary(ffprobe_path, "ffprobe")
    codec = codec_name(video, ffprobe, timeout)
    output.mkdir(parents=True, exist_ok=False)

    if codec != "hevc":
        result: dict[str, object] = {
            "schema_version": 1,
            "module": "hevc_migration_stage",
            "status": "skipped_non_hevc",
            "input": str(video),
            "codec_name": codec,
        }
    else:
        annex_b = output / "source.h265"
        extraction = extract_annex_b(video, annex_b, ffmpeg, timeout)
        legacy_output = output / "legacy_comparison.json"
        export_legacy(annex_b, legacy_output)
        effective_legacy_json = legacy_json or legacy_output
        authority_root = output / "parser_authority"
        authority = run_authority(
            annex_b,
            authority_root,
            repository=repository,
            wrapper=wrapper,
            h265nal=h265nal,
            ffprobe=str(ffprobe),
            legacy_json=effective_legacy_json,
            timeout=timeout,
        )
        reference = run_reference_compare(
            annex_b,
            output / "reference_comparison",
            repository=repository,
            ffmpeg=ffmpeg,
            ffprobe=str(ffprobe),
            wrapper=wrapper,
            h265nal=h265nal,
            legacy_json=effective_legacy_json,
            timeout=timeout,
        )
        result = {
            "schema_version": 1,
            "module": "hevc_migration_stage",
            "status": "completed",
            "input": str(video),
            "codec_name": codec,
            "annex_b": str(annex_b),
            "extraction": extraction,
            "primary_backend": "h265nal",
            "control_backend": "ffprobe",
            "legacy_backend_role": "comparison_only",
            "legacy_comparison_manifest": str(effective_legacy_json),
            "authoritative_for_high_weight": authority["comparison"][
                "authoritative_for_high_weight"
            ],
            "authority_manifest": str(authority_root / "parser_authority.json"),
            "reference_comparison_manifest": str(output / "reference_comparison" / "reference_comparison.json"),
            "legacy_removal_ready": reference["migration_acceptance"]["ready_for_legacy_removal"],
        }
    (output / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-hevc-migration-stage")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--wrapper")
    parser.add_argument("--h265nal")
    parser.add_argument("--legacy-json", type=Path)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    try:
        result = run_stage(
            args.video,
            args.output,
            repository=args.repository,
            ffmpeg_path=args.ffmpeg,
            ffprobe_path=args.ffprobe,
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
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

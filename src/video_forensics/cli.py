from __future__ import annotations

import argparse
import sys
from pathlib import Path

from video_forensics import __version__
from video_forensics.manifest import atomic_write_json, base_manifest, utc_now
from video_forensics.tools import container_structure, gop, integrity, metadata, timeline

SUPPORTED_STAGES = ("integrity", "metadata", "container_structure", "timeline", "gop")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video-forensics")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    analyze = sub.add_parser("analyze", help="run the forensic analysis pipeline")
    analyze.add_argument("video", type=Path)
    analyze.add_argument("--output", required=True, type=Path)
    analyze.add_argument("--stages", default=",".join(SUPPORTED_STAGES), help="comma-separated stages; supported: " + ", ".join(SUPPORTED_STAGES))
    sub.add_parser("tools", help="list available analytical tools")
    return parser


def _parse_stages(raw: str) -> list[str]:
    stages = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(stages) - set(SUPPORTED_STAGES))
    if unknown:
        raise ValueError(f"unsupported stages: {', '.join(unknown)}")
    if not stages:
        raise ValueError("at least one stage is required")
    if len(stages) != len(set(stages)):
        raise ValueError("stages cannot be repeated")
    return stages


def run_analysis(video: Path, output: Path, stages: list[str]) -> int:
    video = video.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifestation = base_manifest(video, sys.argv, __version__)
    manifest_path = output / "manifest.json"
    atomic_write_json(manifest_path, manifestation)
    try:
        if "integrity" in stages:
            manifestation["stages"]["integrity"] = integrity.analyze(video, output)
        if "metadata" in stages:
            metadata_result = metadata.analyze(video, output)
            manifestation["stages"]["metadata"] = metadata_result
            manifestation["tools"].update(metadata_result["tools"])
        if "container_structure" in stages:
            manifestation["stages"]["container_structure"] = container_structure.analyze(video, output)
        if "timeline" in stages:
            manifestation["stages"]["timeline"] = timeline.analyze(video, output)
        if "gop" in stages:
            manifestation["stages"]["gop"] = gop.analyze(video, output)
        manifestation["run"]["status"] = "completed"
        manifestation["run"]["completed_at_utc"] = utc_now()
        return 0
    except Exception as exc:
        manifestation["run"]["status"] = "failed"
        manifestation["run"]["completed_at_utc"] = utc_now()
        manifestation["run"]["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        atomic_write_json(manifest_path, manifestation)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "tools":
        print("\n".join(SUPPORTED_STAGES))
        return 0
    try:
        return run_analysis(args.video, args.output, _parse_stages(args.stages))
    except (FileNotFoundError, PermissionError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

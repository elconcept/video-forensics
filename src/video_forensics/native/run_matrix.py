from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from video_forensics.native.decoder_matrix import execute, find_binary
from video_forensics.native.host_profile import write_profile

PROFILE_ROOT = Path("profiles/decoder_matrix")

PLATFORM_PROFILES = {
    "Linux": (
        "software_single_thread.json",
        "software_automatic_threads.json",
        "linux_nvdec.json",
        "linux_vaapi.json",
        "linux_qsv.json",
    ),
    "Windows": (
        "software_single_thread.json",
        "software_automatic_threads.json",
        "windows_intel_qsv.json",
        "windows_intel_d3d11va.json",
        "windows_nvidia_d3d11va.json",
        "windows_nvidia_cuda.json",
    ),
    "Darwin": (
        "software_single_thread.json",
        "software_automatic_threads.json",
        "macos_videotoolbox.json",
    ),
}


def command_available(argv: list[str], timeout: int = 30) -> bool:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def ffmpeg_text(ffmpeg: Path, option: str) -> str:
    completed = subprocess.run(
        [str(ffmpeg), "-hide_banner", option],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return completed.stdout + completed.stderr


def profile_supported(profile: dict[str, Any], ffmpeg: Path) -> tuple[bool, str]:
    requirement = profile.get("requires")
    if not isinstance(requirement, dict):
        return True, "no explicit capability requirement"

    hwaccel = requirement.get("hwaccel")
    if hwaccel:
        available = ffmpeg_text(ffmpeg, "-hwaccels").lower().split()
        if str(hwaccel).lower() not in available:
            return False, f"FFmpeg does not list hwaccel {hwaccel}"

    decoder = requirement.get("decoder")
    if decoder:
        decoder_text = ffmpeg_text(ffmpeg, "-decoders").lower()
        if str(decoder).lower() not in decoder_text:
            return False, f"FFmpeg does not list decoder {decoder}"

    device = requirement.get("device")
    if isinstance(device, list) and not command_available([str(value) for value in device]):
        return False, "required device probe failed"

    return True, "declared requirements available"


def load_profile(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"profile must be a JSON object: {path}")
    return payload


def selected_profiles(system: str, profile_root: Path) -> list[Path]:
    names = PLATFORM_PROFILES.get(system)
    if names is None:
        names = (
            "software_single_thread.json",
            "software_automatic_threads.json",
        )
    return [profile_root / name for name in names]


def run_matrix(
    video: Path,
    output: Path,
    *,
    ffmpeg: Path,
    ffprobe: Path,
    profile_root: Path,
    timeout: int,
) -> dict[str, object]:
    video = video.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    host_profile_path = output / "host_profile.json"
    host_profile = write_profile(host_profile_path)
    host_profile_id = str(host_profile["host_profile_id"])
    system = platform.system()

    results: list[dict[str, object]] = []
    for path in selected_profiles(system, profile_root):
        if not path.is_file():
            results.append(
                {
                    "profile_file": str(path),
                    "status": "unavailable",
                    "reason": "profile file absent",
                }
            )
            continue
        profile = load_profile(path)
        supported, reason = profile_supported(profile, ffmpeg)
        profile_id = str(profile["profile_id"])
        if not supported:
            results.append(
                {
                    "profile_id": profile_id,
                    "profile_file": str(path),
                    "status": "unavailable",
                    "reason": reason,
                }
            )
            continue
        try:
            run_output = execute(
                video,
                path,
                output / "runs",
                ffmpeg,
                ffprobe,
                timeout,
            )
        except (FileNotFoundError, FileExistsError, KeyError, subprocess.TimeoutExpired, TypeError, ValueError) as exc:
            results.append(
                {
                    "profile_id": profile_id,
                    "profile_file": str(path),
                    "status": "failed",
                    "reason": str(exc),
                }
            )
            continue
        results.append(
            {
                "profile_id": profile_id,
                "profile_file": str(path),
                "status": "completed",
                "output": str(run_output),
            }
        )

    manifest: dict[str, object] = {
        "schema_version": 1,
        "module": "run_matrix",
        "started_and_completed_at_utc": datetime.now(UTC).isoformat(),
        "input": {
            "path": str(video),
            "size_bytes": video.stat().st_size,
        },
        "host_profile_id": host_profile_id,
        "host_profile": str(host_profile_path),
        "platform": system,
        "profiles": results,
        "summary": {
            "completed": sum(item["status"] == "completed" for item in results),
            "failed": sum(item["status"] == "failed" for item in results),
            "unavailable": sum(item["status"] == "unavailable" for item in results),
        },
    }
    (output / "matrix_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-run-matrix")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile-root", type=Path, default=PROFILE_ROOT)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--ffprobe")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        manifest = run_matrix(
            args.video,
            args.output,
            ffmpeg=find_binary("ffmpeg", args.ffmpeg),
            ffprobe=find_binary("ffprobe", args.ffprobe),
            profile_root=args.profile_root,
            timeout=args.timeout,
        )
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

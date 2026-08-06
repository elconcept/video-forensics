from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any

SHOWINFO = re.compile(
    r"showinfo.*?\bn:\s*(?P<n>\d+).*?\bpts:\s*(?P<pts>-?\d+).*?"
    r"\bpts_time:\s*(?P<pts_time>-?(?:\d+(?:\.\d*)?|\.\d+))"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def find_ffmpeg(explicit: str | None) -> Path:
    candidate = explicit or shutil.which("ffmpeg")
    if not candidate:
        raise FileNotFoundError("cannot find ffmpeg; pass --ffmpeg")
    return Path(candidate).expanduser().resolve(strict=True)


def load_profile(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"profile must be a JSON object: {path}")
    return payload


def hardware_download_filter(arguments: list[str]) -> str | None:
    joined = " ".join(arguments).lower()
    if any(name in joined for name in ("d3d11va", "qsv", "cuda", "vaapi")):
        return "hwdownload,format=nv12"
    return None


def build_command(
    ffmpeg: Path,
    video: Path,
    decoder_args: list[str],
) -> list[str]:
    filters: list[str] = []
    download = hardware_download_filter(decoder_args)
    if download:
        filters.append(download)
    filters.append("showinfo")
    return [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "info",
        "-err_detect",
        "ignore_err",
        *decoder_args,
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-vf",
        ",".join(filters),
        "-vsync",
        "0",
        "-f",
        "null",
        "-",
    ]


def parse_showinfo(text: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for match in SHOWINFO.finditer(text):
        rows.append(
            {
                "frame_number": int(match.group("n")) + 1,
                "decoder_frame_index": int(match.group("n")),
                "pts": int(match.group("pts")),
                "pts_time": float(match.group("pts_time")),
            }
        )
    return rows


def analyze(
    video: Path,
    profile_path: Path,
    output: Path,
    *,
    ffmpeg: Path,
    host_profile_id: str | None,
    timeout: int,
) -> dict[str, object]:
    video = video.expanduser().resolve(strict=True)
    profile_path = profile_path.expanduser().resolve(strict=True)
    profile = load_profile(profile_path)
    profile_id = str(profile["profile_id"])
    decoder_args = [str(value) for value in profile["ffmpeg_args"]]
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    argv = build_command(ffmpeg, video, decoder_args)
    started = monotonic()
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    rows = parse_showinfo(completed.stderr)
    (output / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    columns = ["frame_number", "decoder_frame_index", "pts", "pts_time"]
    with (output / "frame_timestamps.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    result: dict[str, object] = {
        "schema_version": 1,
        "module": "decoder_frame_timestamps",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "completed" if completed.returncode == 0 else "decoder_error",
        "duration_seconds": round(monotonic() - started, 6),
        "host_profile": host_profile_id,
        "profile_id": profile_id,
        "profile_file": str(profile_path),
        "input": {
            "path": str(video),
            "size_bytes": video.stat().st_size,
            "sha256": sha256(video),
        },
        "command": argv,
        "returncode": completed.returncode,
        "frame_count": len(rows),
        "frames": rows,
        "interpretation_boundary": (
            "Rows follow the output ordering of this exact decoder invocation. They must be "
            "paired only with images exported through the same profile and ordering options."
        ),
    }
    (output / "decoder_frame_timestamps.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-decoder-frame-timestamps")
    parser.add_argument("video", type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--host-profile-id")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = analyze(
            args.video,
            args.profile,
            args.output,
            ffmpeg=find_ffmpeg(args.ffmpeg),
            host_profile_id=args.host_profile_id,
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "frame_count": result["frame_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

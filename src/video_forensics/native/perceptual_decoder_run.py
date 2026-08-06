from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from time import monotonic

WIDTH = 192
HEIGHT = 108
FRAME_BYTES = WIDTH * HEIGHT


def find_binary(name: str, explicit: str | None) -> Path:
    candidate = explicit or shutil.which(name)
    if not candidate:
        raise FileNotFoundError(f"cannot find {name}; pass --{name}")
    return Path(candidate).expanduser().resolve(strict=True)


def load_profile(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"profile must be a JSON object: {path}")
    return payload


def normalized_filter(ffmpeg_args: list[str]) -> str:
    hardware = any(value in ffmpeg_args for value in ("cuda", "qsv", "d3d11va"))
    prefix = "hwdownload,format=nv12," if hardware else ""
    return f"{prefix}scale={WIDTH}:{HEIGHT}:flags=area,format=gray"


def execute(
    video: Path,
    profile_path: Path,
    output_root: Path,
    ffmpeg: Path,
    timeout: int,
) -> Path:
    profile = load_profile(profile_path)
    profile_id = str(profile["profile_id"])
    ffmpeg_args = [str(value) for value in profile["ffmpeg_args"]]
    video = video.expanduser().resolve(strict=True)
    output = output_root.expanduser().resolve() / f"{profile_id}_perceptual"
    frames_dir = output / "frames"
    frames_dir.mkdir(parents=True, exist_ok=False)

    argv = [
        str(ffmpeg), "-nostdin", "-hide_banner", "-loglevel", "repeat+level+verbose",
        *ffmpeg_args, "-i", str(video), "-map", "0:v:0", "-vf",
        normalized_filter(ffmpeg_args), "-vsync", "0", "-f", "rawvideo",
        "-pix_fmt", "gray", "-",
    ]
    started = monotonic()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise RuntimeError("failed to open FFmpeg pipes")

    rows: list[dict[str, object]] = []
    try:
        while True:
            if monotonic() - started > timeout:
                process.kill()
                raise TimeoutError(f"perceptual decode exceeded {timeout} seconds")
            data = process.stdout.read(FRAME_BYTES)
            if not data:
                break
            if len(data) != FRAME_BYTES:
                process.kill()
                raise RuntimeError(
                    f"incomplete normalized frame: expected {FRAME_BYTES}, got {len(data)}"
                )
            frame_number = len(rows) + 1
            filename = f"frame_{frame_number:09d}.gray"
            (frames_dir / filename).write_bytes(data)
            rows.append({
                "frame_number": frame_number,
                "filename": filename,
                "sha256": hashlib.sha256(data).hexdigest(),
            })
    finally:
        process.stdout.close()

    stderr = process.stderr.read().decode("utf-8", errors="replace")
    process.stderr.close()
    returncode = process.wait()
    (output / "stderr.txt").write_text(stderr, encoding="utf-8")
    with (output / "frames.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["frame_number", "filename", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "schema_version": 1,
        "profile_id": profile_id,
        "input": {"path": str(video), "size_bytes": video.stat().st_size},
        "normalization": {"width": WIDTH, "height": HEIGHT, "pixel_format": "gray"},
        "command": argv,
        "returncode": returncode,
        "duration_seconds": round(monotonic() - started, 6),
        "frame_count": len(rows),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(prog="perceptual-decoder-run")
    parser.add_argument("video", type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    try:
        output = execute(
            args.video, args.profile, args.output,
            find_binary("ffmpeg", args.ffmpeg), args.timeout,
        )
    except (FileNotFoundError, FileExistsError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

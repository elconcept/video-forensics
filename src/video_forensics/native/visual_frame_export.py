from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any

LOSSLESS_FORMAT = "png"
EMAIL_FORMAT = "jpg"
EMAIL_SCALE = "1280:-2"
EMAIL_QSCALE = "3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def find_binary(name: str, explicit: str | None) -> Path:
    candidate = explicit or shutil.which(name)
    if not candidate:
        raise FileNotFoundError(f"cannot find {name}; pass --{name}")
    return Path(candidate).expanduser().resolve(strict=True)


def load_profile(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"profile must be a JSON object: {path}")
    return payload


def hardware_download_filter(arguments: list[str]) -> str | None:
    joined = " ".join(arguments).lower()
    if "d3d11va" in joined:
        return "hwdownload,format=nv12"
    if "qsv" in joined:
        return "hwdownload,format=nv12"
    if "cuda" in joined:
        return "hwdownload,format=nv12"
    if "videotoolbox" in joined:
        return None
    return None


def run_command(argv: list[str], timeout: int) -> dict[str, object]:
    started = monotonic()
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_seconds": round(monotonic() - started, 6),
    }


def export_command(
    ffmpeg: Path,
    video: Path,
    ffmpeg_args: list[str],
    output_pattern: Path,
    *,
    email: bool,
) -> list[str]:
    filters: list[str] = []
    download = hardware_download_filter(ffmpeg_args)
    if download:
        filters.append(download)
    if email:
        filters.append(f"scale={EMAIL_SCALE}:flags=lanczos")

    argv = [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "repeat+level+verbose",
        "-err_detect",
        "ignore_err",
        *ffmpeg_args,
        "-i",
        str(video),
        "-map",
        "0:v:0",
    ]
    if filters:
        argv.extend(["-vf", ",".join(filters)])
    argv.extend(["-vsync", "0", "-start_number", "1"])
    if email:
        argv.extend(["-c:v", "mjpeg", "-q:v", EMAIL_QSCALE])
    else:
        argv.extend(["-c:v", "png", "-compression_level", "6"])
    argv.extend(["-f", "image2", str(output_pattern)])
    return argv


def inventory(directory: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in directory.iterdir() if item.is_file()):
        rows.append(
            {
                "frame_number": len(rows) + 1,
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def write_index(path: Path, rows: list[dict[str, object]]) -> None:
    columns = ["frame_number", "filename", "size_bytes", "sha256"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def export_profile(
    video: Path,
    profile_path: Path,
    output_root: Path,
    ffmpeg: Path,
    host_profile_id: str,
    timeout: int,
) -> dict[str, object]:
    profile = load_profile(profile_path)
    profile_id = str(profile["profile_id"])
    ffmpeg_args = [str(value) for value in profile["ffmpeg_args"]]
    run_id = f"{host_profile_id}__{profile_id}"
    lossless_dir = output_root / "lossless" / run_id
    email_dir = output_root / "email" / run_id
    lossless_dir.mkdir(parents=True, exist_ok=False)
    email_dir.mkdir(parents=True, exist_ok=False)

    lossless_command = export_command(
        ffmpeg,
        video,
        ffmpeg_args,
        lossless_dir / "frame_%09d.png",
        email=False,
    )
    email_command = export_command(
        ffmpeg,
        video,
        ffmpeg_args,
        email_dir / "frame_%09d.jpg",
        email=True,
    )
    lossless_result = run_command(lossless_command, timeout)
    email_result = run_command(email_command, timeout)
    (lossless_dir / "stderr.txt").write_text(
        str(lossless_result["stderr"]), encoding="utf-8"
    )
    (email_dir / "stderr.txt").write_text(
        str(email_result["stderr"]), encoding="utf-8"
    )

    lossless_rows = inventory(lossless_dir)
    email_rows = inventory(email_dir)
    write_index(lossless_dir / "index.csv", lossless_rows)
    write_index(email_dir / "index.csv", email_rows)
    return {
        "run_id": run_id,
        "profile_id": profile_id,
        "lossless": {
            "returncode": lossless_result["returncode"],
            "command": lossless_command,
            "frame_count": sum(row["filename"].endswith(".png") for row in lossless_rows),
            "directory": str(lossless_dir),
        },
        "email": {
            "returncode": email_result["returncode"],
            "command": email_command,
            "frame_count": sum(row["filename"].endswith(".jpg") for row in email_rows),
            "directory": str(email_dir),
        },
    }


def export_all(
    video: Path,
    profiles: list[Path],
    output: Path,
    ffmpeg: Path,
    host_profile: Path,
    timeout: int,
) -> dict[str, object]:
    video = video.expanduser().resolve(strict=True)
    host = load_profile(host_profile.expanduser().resolve(strict=True))
    host_profile_id = str(host["host_profile_id"])
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    runs = [
        export_profile(video, profile, output, ffmpeg, host_profile_id, timeout)
        for profile in profiles
    ]
    result: dict[str, object] = {
        "schema_version": 1,
        "module": "visual_frame_export",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input": {
            "path": str(video),
            "size_bytes": video.stat().st_size,
            "sha256": sha256(video),
        },
        "host_profile_id": host_profile_id,
        "host_profile": str(host_profile),
        "lossless_policy": {
            "format": LOSSLESS_FORMAT,
            "resolution": "decoded native resolution",
            "purpose": "complete derivative set for technical verification and human review",
        },
        "email_policy": {
            "format": EMAIL_FORMAT,
            "maximum_width": 1280,
            "aspect_ratio_preserved": True,
            "ffmpeg_qscale": int(EMAIL_QSCALE),
            "purpose": "compressed review copy for email submission",
            "notice": (
                "Compressed review derivatives. Lossless PNG derivatives are retained and "
                "can be supplied on request. The source recording remains the primary evidence."
            ),
        },
        "runs": runs,
    }
    (output / "visual_frame_export.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "README_EMAIL_COPY.txt").write_text(
        "Kopie skompresowane do przeglądu i przesłania pocztą elektroniczną.\n"
        "Bezstratne pochodne PNG zachowano i mogą zostać przekazane na żądanie.\n"
        "Plik źródłowy pozostaje materiałem podstawowym.\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-export-visual-frames")
    parser.add_argument("video", type=Path)
    parser.add_argument("--profile", action="append", required=True, type=Path)
    parser.add_argument("--host-profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = export_all(
            args.video,
            args.profile,
            args.output,
            find_binary("ffmpeg", args.ffmpeg),
            args.host_profile,
            args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        KeyError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"run_count": len(result["runs"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

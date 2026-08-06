from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic


@dataclass(frozen=True)
class Profile:
    profile_id: str
    description: str
    ffmpeg_args: list[str]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


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


def load_profile(path: Path) -> Profile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"profile must be a JSON object: {path}")
    return Profile(
        profile_id=str(payload["profile_id"]),
        description=str(payload["description"]),
        ffmpeg_args=[str(value) for value in payload["ffmpeg_args"]],
    )


def run(argv: list[str], timeout: int) -> dict[str, object]:
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


def version(binary: Path) -> str:
    completed = subprocess.run(
        [str(binary), "-version"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return output.splitlines()[0] if output else "unknown"


def hardware_inventory(ffmpeg: Path) -> dict[str, object]:
    inventory: dict[str, object] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "ffmpeg_version": version(ffmpeg),
    }
    if platform.system() == "Windows":
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            ("Get-CimInstance Win32_VideoController | "
            "Select-Object Name,PNPDeviceID,DriverVersion,AdapterRAM | ConvertTo-Json"),
        ]
        result = run(command, 60)
        inventory["windows_video_controllers"] = result
    inventory["ffmpeg_hwaccels"] = run([str(ffmpeg), "-hide_banner", "-hwaccels"], 60)
    inventory["ffmpeg_decoders"] = run([str(ffmpeg), "-hide_banner", "-decoders"], 60)
    return inventory


def decoded_frame_count(ffprobe: Path, directory: Path) -> int:
    return len(list(directory.glob("frame_*.framemd5")))


def execute(
    video: Path,
    profile_path: Path,
    output_root: Path,
    ffmpeg: Path,
    ffprobe: Path,
    timeout: int,
) -> Path:
    profile = load_profile(profile_path)
    video = video.expanduser().resolve(strict=True)
    output = output_root.expanduser().resolve() / profile.profile_id
    output.mkdir(parents=True, exist_ok=False)

    manifest: dict[str, object] = {
        "schema_version": 1,
        "started_at_utc": utc_now(),
        "profile": asdict(profile),
        "input": {
            "path": str(video),
            "size_bytes": video.stat().st_size,
            "sha256": sha256(video),
        },
        "inventory": hardware_inventory(ffmpeg),
    }

    command = [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "repeat+level+verbose",
        *profile.ffmpeg_args,
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-vsync",
        "0",
        "-f",
        "framemd5",
        str(output / "frames.framemd5"),
    ]
    decode = run(command, timeout)
    (output / "stdout.txt").write_text(str(decode["stdout"]), encoding="utf-8")
    (output / "stderr.txt").write_text(str(decode["stderr"]), encoding="utf-8")
    manifest["decode"] = {
        "argv": decode["argv"],
        "returncode": decode["returncode"],
        "duration_seconds": decode["duration_seconds"],
        "framemd5_exists": (output / "frames.framemd5").is_file(),
    }
    manifest["ffprobe_version"] = version(ffprobe)
    manifest["completed_at_utc"] = utc_now()
    manifest["status"] = "completed" if decode["returncode"] == 0 else "decoder_error"
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="decoder-matrix")
    result.add_argument("video", type=Path)
    result.add_argument("--profile", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    result.add_argument("--ffmpeg")
    result.add_argument("--ffprobe")
    result.add_argument("--timeout", type=int, default=3600)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        output = execute(
            args.video,
            args.profile,
            args.output,
            find_binary("ffmpeg", args.ffmpeg),
            find_binary("ffprobe", args.ffprobe),
            args.timeout,
        )
    except (FileNotFoundError, FileExistsError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

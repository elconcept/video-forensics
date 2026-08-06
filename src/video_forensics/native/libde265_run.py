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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def find_dec265(explicit: str | None) -> Path | None:
    candidates = [explicit] if explicit else ["dec265", "de265dec"]
    for candidate in candidates:
        if not candidate:
            continue
        located = shutil.which(candidate) if Path(candidate).name == candidate else candidate
        if located:
            return Path(located).expanduser().resolve(strict=True)
    return None


def version(binary: Path) -> dict[str, object]:
    for arguments in (["--version"], ["-h"]):
        completed = subprocess.run(
            [str(binary), *arguments],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        text = completed.stdout.strip() or completed.stderr.strip()
        if text:
            return {
                "argv": [str(binary), *arguments],
                "returncode": completed.returncode,
                "first_line": text.splitlines()[0],
                "output": text,
            }
    return {"argv": [str(binary)], "returncode": None, "first_line": "unknown"}


def frame_size(width: int, height: int, pixel_format: str) -> int:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if pixel_format == "yuv420p":
        if width % 2 or height % 2:
            raise ValueError("yuv420p requires even width and height")
        return width * height * 3 // 2
    if pixel_format == "yuv444p":
        return width * height * 3
    if pixel_format == "gray":
        return width * height
    raise ValueError(f"unsupported pixel format: {pixel_format}")


def frame_inventory(path: Path, bytes_per_frame: int) -> list[dict[str, object]]:
    size = path.stat().st_size
    if size % bytes_per_frame:
        raise ValueError(
            f"decoded YUV size is not divisible by frame size: {size} % {bytes_per_frame}"
        )
    rows: list[dict[str, object]] = []
    with path.open("rb") as handle:
        frame_number = 0
        while data := handle.read(bytes_per_frame):
            frame_number += 1
            rows.append(
                {
                    "frame_number": frame_number,
                    "offset": (frame_number - 1) * bytes_per_frame,
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    columns = ["frame_number", "offset", "size_bytes", "sha256"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def run_decode(
    annex_b: Path,
    output: Path,
    *,
    binary: Path | None,
    width: int,
    height: int,
    pixel_format: str,
    threads: int,
    host_profile_id: str | None,
    timeout: int,
) -> dict[str, object]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = {
        "path": str(annex_b),
        "size_bytes": annex_b.stat().st_size,
        "sha256": sha256(annex_b),
    }
    if binary is None:
        result: dict[str, object] = {
            "schema_version": 1,
            "module": "libde265_run",
            "status": "unavailable",
            "reason": "dec265/de265dec executable not found",
            "host_profile": host_profile_id,
            "source": source,
        }
    else:
        if threads < 0:
            raise ValueError("threads must be zero or positive")
        bytes_per_frame = frame_size(width, height, pixel_format)
        yuv = output / "decoded.yuv"
        argv = [
            str(binary),
            "-q",
            "-t",
            str(threads),
            "-o",
            str(yuv),
            str(annex_b),
        ]
        started = monotonic()
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        (output / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (output / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
        rows = frame_inventory(yuv, bytes_per_frame) if yuv.is_file() else []
        if rows:
            write_csv(output / "frames.csv", rows)
        result = {
            "schema_version": 1,
            "module": "libde265_run",
            "status": "completed" if completed.returncode == 0 else "decoder_error",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(monotonic() - started, 6),
            "host_profile": host_profile_id,
            "source": source,
            "tool": {"path": str(binary), "version": version(binary)},
            "command": argv,
            "returncode": completed.returncode,
            "geometry": {
                "width": width,
                "height": height,
                "pixel_format": pixel_format,
                "bytes_per_frame": bytes_per_frame,
                "analyst_supplied": True,
            },
            "decoded_yuv": {
                "path": str(yuv),
                "exists": yuv.is_file(),
                "size_bytes": yuv.stat().st_size if yuv.is_file() else 0,
                "sha256": sha256(yuv) if yuv.is_file() else None,
            },
            "frame_count": len(rows),
            "frames": rows,
            "interpretation_boundary": (
                "Frame boundaries depend on analyst-supplied output geometry and pixel format. "
                "These parameters must be verified against parsed SPS and decoder output."
            ),
        }
    (output / "libde265_run.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-libde265-run")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument(
        "--pixel-format", choices=("yuv420p", "yuv444p", "gray"), default="yuv420p"
    )
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--dec265")
    parser.add_argument("--host-profile-id")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = run_decode(
            args.annex_b,
            args.output,
            binary=find_dec265(args.dec265),
            width=args.width,
            height=args.height,
            pixel_format=args.pixel_format,
            threads=args.threads,
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
    print(json.dumps({"status": result["status"], "frame_count": result.get("frame_count")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

TIMESTAMP_PATTERN = re.compile(
    r"(?P<day>\d{2})[-./](?P<month>\d{2})[-./](?P<year>\d{4})\s+"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def find_tesseract(explicit: str | None) -> Path | None:
    candidate = explicit or shutil.which("tesseract")
    return None if candidate is None else Path(candidate).expanduser().resolve(strict=True)


def parse_timestamp(text: str) -> datetime | None:
    match = TIMESTAMP_PATTERN.search(text)
    if match is None:
        return None
    values = {name: int(value) for name, value in match.groupdict().items()}
    try:
        return datetime(
            values["year"],
            values["month"],
            values["day"],
            values["hour"],
            values["minute"],
            values["second"],
            tzinfo=UTC,
        )
    except ValueError:
        return None


def preprocess(image: Image.Image, scale: int) -> Image.Image:
    gray = ImageOps.grayscale(image)
    if scale > 1:
        gray = gray.resize(
            (gray.width * scale, gray.height * scale), Image.Resampling.LANCZOS
        )
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    return gray.filter(ImageFilter.SHARPEN)


def crop_image(image: Image.Image, crop: tuple[int, int, int, int]) -> Image.Image:
    x, y, width, height = crop
    if min(x, y) < 0 or width <= 0 or height <= 0:
        raise ValueError("invalid OSD crop geometry")
    if x + width > image.width or y + height > image.height:
        raise ValueError("OSD crop exceeds frame bounds")
    return image.crop((x, y, x + width, y + height))


def ocr_frame(
    frame: Path,
    tesseract: Path,
    crop: tuple[int, int, int, int],
    scale: int,
    language: str,
    timeout: int,
) -> tuple[str, list[str], str]:
    with Image.open(frame) as image:
        prepared = preprocess(crop_image(image, crop), scale)
        with tempfile.TemporaryDirectory(prefix="osd-reader-") as temporary:
            temporary_path = Path(temporary)
            input_path = temporary_path / "crop.png"
            prepared.save(input_path, format="PNG")
            argv = [
                str(tesseract),
                str(input_path),
                "stdout",
                "-l",
                language,
                "--psm",
                "7",
                "-c",
                "tessedit_char_whitelist=0123456789-./:()W ",
            ]
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Tesseract failed")
    return completed.stdout.strip(), argv, completed.stderr


def frame_files(root: Path) -> list[Path]:
    files = sorted(
        path
        for path in root.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    )
    if not files:
        raise ValueError(f"no image frames found: {root}")
    return files


def analyze_readings(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    previous: datetime | None = None
    previous_frame: int | None = None
    missing_start: int | None = None
    for row in rows:
        frame_number = int(row["frame_number"])
        parsed_text = row.get("parsed_timestamp")
        current = None if parsed_text is None else datetime.fromisoformat(str(parsed_text))
        if current is None:
            if missing_start is None:
                missing_start = frame_number
            continue
        if missing_start is not None:
            findings.append(
                {
                    "id": "OSD_TIMESTAMP_ABSENT_RANGE",
                    "severity": "low",
                    "description": "No timestamp was parsed for a contiguous frame range.",
                    "start_frame": missing_start,
                    "end_frame": frame_number - 1,
                }
            )
            missing_start = None
        if previous is not None and current < previous:
            findings.append(
                {
                    "id": "OSD_TIMESTAMP_NON_MONOTONIC",
                    "severity": "medium",
                    "description": "Parsed burned-in timestamp moved backwards.",
                    "previous_frame": previous_frame,
                    "current_frame": frame_number,
                    "previous_timestamp": previous.isoformat(),
                    "current_timestamp": current.isoformat(),
                    "delta_seconds": (current - previous).total_seconds(),
                }
            )
        previous = current
        previous_frame = frame_number
    if missing_start is not None:
        findings.append(
            {
                "id": "OSD_TIMESTAMP_ABSENT_RANGE",
                "severity": "low",
                "description": "No timestamp was parsed for a contiguous frame range.",
                "start_frame": missing_start,
                "end_frame": int(rows[-1]["frame_number"]),
            }
        )
    return findings


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    columns = [
        "frame_number",
        "filename",
        "sha256",
        "ocr_text",
        "parsed_timestamp",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def analyze(
    frames_root: Path,
    output: Path,
    *,
    crop: tuple[int, int, int, int],
    scale: int,
    language: str,
    tesseract: Path | None,
    host_profile_id: str | None,
    timeout: int,
) -> dict[str, object]:
    frames_root = frames_root.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    frames = frame_files(frames_root)
    if tesseract is None:
        result: dict[str, object] = {
            "schema_version": 1,
            "module": "osd_reader",
            "status": "unavailable",
            "reason": "tesseract executable not found",
            "host_profile": host_profile_id,
            "frame_count": len(frames),
        }
    else:
        rows: list[dict[str, object]] = []
        diagnostics: list[dict[str, object]] = []
        for frame_number, frame in enumerate(frames, start=1):
            text, argv, stderr = ocr_frame(
                frame, tesseract, crop, scale, language, timeout
            )
            parsed = parse_timestamp(text)
            rows.append(
                {
                    "frame_number": frame_number,
                    "filename": frame.name,
                    "sha256": sha256(frame),
                    "ocr_text": text,
                    "parsed_timestamp": None if parsed is None else parsed.isoformat(),
                }
            )
            diagnostics.append(
                {"frame_number": frame_number, "command": argv, "stderr": stderr}
            )
        findings = analyze_readings(rows)
        write_csv(output / "readings.csv", rows)
        result = {
            "schema_version": 1,
            "module": "osd_reader",
            "status": "completed",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "host_profile": host_profile_id,
            "parameters": {
                "crop": {"x": crop[0], "y": crop[1], "width": crop[2], "height": crop[3]},
                "scale": scale,
                "language": language,
                "page_segmentation_mode": 7,
            },
            "frame_count": len(rows),
            "parsed_count": sum(row["parsed_timestamp"] is not None for row in rows),
            "finding_count": len(findings),
            "readings": rows,
            "findings": findings,
            "diagnostics": diagnostics,
            "interpretation_boundary": (
                "OCR readings are machine interpretations of burned-in pixels and require visual "
                "confirmation. Typeface and glyph-metric inconsistency are not yet implemented."
            ),
        }
    (output / "osd_reader.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-osd-reader")
    parser.add_argument("frames_root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--crop", required=True, nargs=4, type=int, metavar=("X", "Y", "W", "H"))
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--language", default="eng")
    parser.add_argument("--tesseract")
    parser.add_argument("--host-profile-id")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.scale <= 0:
        print("ERROR: scale must be positive", file=sys.stderr)
        return 2
    try:
        result = analyze(
            args.frames_root,
            args.output,
            crop=tuple(args.crop),
            scale=args.scale,
            language=args.language,
            tesseract=find_tesseract(args.tesseract),
            host_profile_id=args.host_profile_id,
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "finding_count": result.get("finding_count")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

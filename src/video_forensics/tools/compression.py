from __future__ import annotations

import csv
import statistics
from collections import Counter
from pathlib import Path
from time import monotonic

from video_forensics.manifest import atomic_write_json, utc_now

WINDOW_SIZE = 30
MIN_WINDOW_VALUES = 10
ROBUST_SCORE_LIMIT = 8.0


def _float_or_none(value: object) -> float | None:
    if value in (None, "", "None", "N/A"):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _int_or_none(value: object) -> int | None:
    if value in (None, "", "None", "N/A"):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def _read_frames(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"required GOP output not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _window_rows(rows: list[dict[str, str]], window_size: int = WINDOW_SIZE) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    for start in range(0, len(rows), window_size):
        members = rows[start : start + window_size]
        packet_sizes = [
            value
            for row in members
            if (value := _float_or_none(row.get("pkt_size"))) is not None
        ]
        if not packet_sizes:
            continue
        picture_types = Counter(str(row.get("pict_type") or "unknown") for row in members)
        windows.append(
            {
                "window_number": len(windows) + 1,
                "start_frame": _int_or_none(members[0].get("frame_number")),
                "end_frame": _int_or_none(members[-1].get("frame_number")),
                "frame_count": len(members),
                "packet_size_count": len(packet_sizes),
                "packet_size_mean": round(statistics.fmean(packet_sizes), 6),
                "packet_size_median": round(statistics.median(packet_sizes), 6),
                "packet_size_min": min(packet_sizes),
                "packet_size_max": max(packet_sizes),
                "picture_type_counts": dict(sorted(picture_types.items())),
            }
        )
    return windows


def _mad(values: list[float]) -> tuple[float, float]:
    median = statistics.median(values)
    return median, statistics.median(abs(value - median) for value in values)


def _findings(windows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(windows) < 3:
        return []
    medians = [float(window["packet_size_median"]) for window in windows]
    center, mad = _mad(medians)
    if mad == 0.0:
        return []
    scale = 1.4826 * mad
    findings: list[dict[str, object]] = []
    for window in windows:
        if int(window["packet_size_count"]) < MIN_WINDOW_VALUES:
            continue
        score = abs(float(window["packet_size_median"]) - center) / scale
        if score >= ROBUST_SCORE_LIMIT:
            findings.append(
                {
                    "kind": "packet_size_regime_candidate",
                    "window_number": window["window_number"],
                    "start_frame": window["start_frame"],
                    "end_frame": window["end_frame"],
                    "packet_size_median": window["packet_size_median"],
                    "global_window_median": center,
                    "median_absolute_deviation": mad,
                    "robust_score": round(score, 6),
                }
            )
    return findings


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "window_number",
        "start_frame",
        "end_frame",
        "frame_count",
        "packet_size_count",
        "packet_size_mean",
        "packet_size_median",
        "packet_size_min",
        "packet_size_max",
        "picture_type_counts",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def analyze(video: Path, output_dir: Path) -> dict[str, object]:
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError(f"input is not a regular file: {video}")

    started = monotonic()
    rows = _read_frames(output_dir / "gop" / "frames.csv")
    windows = _window_rows(rows)
    findings = _findings(windows)

    _write_csv(output_dir / "compression" / "windows.csv", windows)
    atomic_write_json(output_dir / "compression" / "findings.json", findings)

    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "compression",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "method": {
            "input": "packet sizes and picture types from GOP stage",
            "window_size_frames": WINDOW_SIZE,
            "minimum_packet_sizes_per_window": MIN_WINDOW_VALUES,
            "robust_score_limit": ROBUST_SCORE_LIMIT,
            "scale": "1.4826 * median absolute deviation of window packet-size medians",
        },
        "scope": {
            "supported": "local packet-size regime screening",
            "not_supported": "macroblock QP, motion vectors, CTU analysis, or double-compression proof",
        },
        "summary": {
            "input_frame_count": len(rows),
            "window_count": len(windows),
            "candidate_count": len(findings),
        },
        "outputs": {
            "windows": "compression/windows.csv",
            "findings": "compression/findings.json",
        },
    }
    atomic_write_json(output_dir / "compression" / "compression.json", result)
    return result

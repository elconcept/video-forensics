from __future__ import annotations

import csv
import math
import subprocess
from collections.abc import Iterator
from pathlib import Path
from time import monotonic

import numpy as np

from video_forensics.manifest import atomic_write_json, utc_now

FFMPEG = Path("/usr/bin/ffmpeg")
ANALYSIS_WIDTH = 480
ANALYSIS_HEIGHT = 270
FRAME_BYTES = ANALYSIS_WIDTH * ANALYSIS_HEIGHT


def _frame_stream(video: Path, *, timeout: int = 3600) -> Iterator[np.ndarray]:
    argv = [
        str(FFMPEG),
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-vf",
        f"scale={ANALYSIS_WIDTH}:{ANALYSIS_HEIGHT}:flags=area,format=gray",
        "-vsync",
        "0",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-",
    ]
    process = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise RuntimeError("failed to open FFmpeg pipes")

    started = monotonic()
    try:
        while True:
            if monotonic() - started > timeout:
                process.kill()
                raise TimeoutError(f"FFmpeg frame decoding exceeded {timeout} seconds")
            buffer = process.stdout.read(FRAME_BYTES)
            if not buffer:
                break
            if len(buffer) != FRAME_BYTES:
                process.kill()
                raise RuntimeError(
                    f"incomplete decoded frame: expected {FRAME_BYTES} bytes, got {len(buffer)}"
                )
            yield np.frombuffer(buffer, dtype=np.uint8).reshape(
                ANALYSIS_HEIGHT, ANALYSIS_WIDTH
            )
    finally:
        process.stdout.close()

    stderr = process.stderr.read().decode("utf-8", errors="replace")
    process.stderr.close()
    returncode = process.wait()
    if returncode != 0:
        diagnostic = stderr.strip() or "no diagnostic output"
        raise RuntimeError(f"FFmpeg frame decoding failed ({returncode}): {diagnostic}")


def _laplacian_variance(frame: np.ndarray) -> float:
    values = frame.astype(np.float32)
    laplacian = (
        -4.0 * values[1:-1, 1:-1]
        + values[:-2, 1:-1]
        + values[2:, 1:-1]
        + values[1:-1, :-2]
        + values[1:-1, 2:]
    )
    return float(laplacian.var())


def _entropy(frame: np.ndarray) -> float:
    counts = np.bincount(frame.ravel(), minlength=256).astype(np.float64)
    probabilities = counts[counts > 0] / frame.size
    return float(-(probabilities * np.log2(probabilities)).sum())


def _metrics(video: Path, *, timeout: int = 3600) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous: np.ndarray | None = None
    for frame_number, frame in enumerate(_frame_stream(video, timeout=timeout), start=1):
        mean = float(frame.mean())
        standard_deviation = float(frame.std())
        mae_previous = None
        if previous is not None:
            mae_previous = float(
                np.abs(frame.astype(np.int16) - previous.astype(np.int16)).mean()
            )
        rows.append(
            {
                "frame_number": frame_number,
                "luma_mean": round(mean, 6),
                "luma_stddev": round(standard_deviation, 6),
                "mae_previous": None if mae_previous is None else round(mae_previous, 6),
                "laplacian_variance": round(_laplacian_variance(frame), 6),
                "entropy": round(_entropy(frame), 6),
            }
        )
        previous = frame.copy()
    return rows


def _summary(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "frame_count": 0,
            "luma_mean_min": None,
            "luma_mean_max": None,
            "mae_previous_max": None,
            "laplacian_variance_min": None,
            "laplacian_variance_max": None,
            "entropy_min": None,
            "entropy_max": None,
        }

    def values(name: str) -> list[float]:
        return [float(row[name]) for row in rows if row[name] is not None]

    luma = values("luma_mean")
    mae = values("mae_previous")
    sharpness = values("laplacian_variance")
    entropy = values("entropy")
    return {
        "frame_count": len(rows),
        "luma_mean_min": min(luma),
        "luma_mean_max": max(luma),
        "mae_previous_max": max(mae) if mae else None,
        "laplacian_variance_min": min(sharpness),
        "laplacian_variance_max": max(sharpness),
        "entropy_min": min(entropy),
        "entropy_max": max(entropy),
    }


def _findings(rows: list[dict[str, object]], limit: int = 20) -> list[dict[str, object]]:
    candidates = [row for row in rows if row["mae_previous"] is not None]
    ranked = sorted(candidates, key=lambda row: float(row["mae_previous"]), reverse=True)
    return [
        {
            "kind": "high_interframe_difference_candidate",
            "frame_number": row["frame_number"],
            "mae_previous": row["mae_previous"],
        }
        for row in ranked[:limit]
        if not math.isnan(float(row["mae_previous"]))
    ]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "frame_number",
        "luma_mean",
        "luma_stddev",
        "mae_previous",
        "laplacian_variance",
        "entropy",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def analyze(video: Path, output_dir: Path, *, timeout: int = 3600) -> dict[str, object]:
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError(f"input is not a regular file: {video}")
    if not FFMPEG.is_file():
        raise FileNotFoundError(f"required executable not found: {FFMPEG}")

    started = monotonic()
    rows = _metrics(video, timeout=timeout)
    findings = _findings(rows)
    _write_csv(output_dir / "frame_metrics" / "metrics.csv", rows)
    atomic_write_json(output_dir / "frame_metrics" / "findings.json", findings)

    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "frame_metrics",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "tool": {"name": "ffmpeg", "executable": str(FFMPEG)},
        "analysis_geometry": {
            "width": ANALYSIS_WIDTH,
            "height": ANALYSIS_HEIGHT,
            "pixel_format": "gray",
        },
        "summary": _summary(rows),
        "finding_count": len(findings),
        "outputs": {
            "metrics": "frame_metrics/metrics.csv",
            "findings": "frame_metrics/findings.json",
        },
    }
    atomic_write_json(output_dir / "frame_metrics" / "frame_metrics.json", result)
    return result

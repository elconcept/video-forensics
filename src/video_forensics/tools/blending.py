from __future__ import annotations

import csv
import subprocess
from collections.abc import Iterator
from pathlib import Path
from time import monotonic

import numpy as np

from video_forensics.manifest import atomic_write_json, utc_now

FFMPEG = Path("/usr/bin/ffmpeg")
WIDTH = 480
HEIGHT = 270
FRAME_BYTES = WIDTH * HEIGHT
RESIDUAL_RATIO_LIMIT = 0.6
MIN_MAE = 2.0


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
        f"scale={WIDTH}:{HEIGHT}:flags=area,format=gray",
        "-vsync",
        "0",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-",
    ]
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise RuntimeError("failed to open FFmpeg pipes")

    started = monotonic()
    try:
        while True:
            if monotonic() - started > timeout:
                process.kill()
                raise TimeoutError(f"FFmpeg blending analysis exceeded {timeout} seconds")
            data = process.stdout.read(FRAME_BYTES)
            if not data:
                break
            if len(data) != FRAME_BYTES:
                process.kill()
                raise RuntimeError(
                    f"incomplete decoded frame: expected {FRAME_BYTES} bytes, got {len(data)}"
                )
            yield np.frombuffer(data, dtype=np.uint8).reshape(HEIGHT, WIDTH)
    finally:
        process.stdout.close()

    stderr = process.stderr.read().decode("utf-8", errors="replace")
    process.stderr.close()
    returncode = process.wait()
    if returncode != 0:
        diagnostic = stderr.strip() or "no diagnostic output"
        raise RuntimeError(f"FFmpeg blending analysis failed ({returncode}): {diagnostic}")


def _fit_blend(previous: np.ndarray, current: np.ndarray, following: np.ndarray) -> dict[str, float]:
    left = previous.astype(np.float32)
    middle = current.astype(np.float32)
    right = following.astype(np.float32)
    direction = left - right
    denominator = float(np.sum(direction * direction))
    if denominator == 0.0:
        alpha = 0.5
    else:
        alpha = float(np.sum((middle - right) * direction) / denominator)
        alpha = max(0.0, min(1.0, alpha))

    predicted = alpha * left + (1.0 - alpha) * right
    residual = float(np.mean(np.abs(middle - predicted)))
    baseline = min(
        float(np.mean(np.abs(middle - left))),
        float(np.mean(np.abs(middle - right))),
    )
    ratio = residual / baseline if baseline > 0.0 else 1.0
    mae_previous = float(np.mean(np.abs(middle - left)))
    mae_following = float(np.mean(np.abs(middle - right)))
    return {
        "alpha": alpha,
        "residual": residual,
        "baseline": baseline,
        "residual_ratio": ratio,
        "mae_previous": mae_previous,
        "mae_following": mae_following,
    }


def _measure(video: Path, *, timeout: int = 3600) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    iterator = iter(_frame_stream(video, timeout=timeout))
    try:
        previous = next(iterator)
        current = next(iterator)
    except StopIteration:
        return rows

    frame_number = 2
    for following in iterator:
        metrics = _fit_blend(previous, current, following)
        rows.append(
            {
                "frame_number": frame_number,
                **{name: round(value, 6) for name, value in metrics.items()},
            }
        )
        previous, current = current, following
        frame_number += 1
    return rows


def _findings(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    findings = []
    for row in rows:
        ratio = float(row["residual_ratio"])
        movement = min(float(row["mae_previous"]), float(row["mae_following"]))
        alpha = float(row["alpha"])
        if ratio <= RESIDUAL_RATIO_LIMIT and movement >= MIN_MAE and 0.05 < alpha < 0.95:
            findings.append(
                {
                    "kind": "linear_blend_candidate",
                    "frame_number": row["frame_number"],
                    "alpha": alpha,
                    "residual": row["residual"],
                    "baseline": row["baseline"],
                    "residual_ratio": ratio,
                    "mae_previous": row["mae_previous"],
                    "mae_following": row["mae_following"],
                }
            )
    return findings


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "frame_number",
        "alpha",
        "residual",
        "baseline",
        "residual_ratio",
        "mae_previous",
        "mae_following",
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
    rows = _measure(video, timeout=timeout)
    findings = _findings(rows)
    _write_csv(output_dir / "blending" / "metrics.csv", rows)
    atomic_write_json(output_dir / "blending" / "findings.json", findings)

    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "blending",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "tool": {"name": "ffmpeg", "executable": str(FFMPEG)},
        "analysis_geometry": {"width": WIDTH, "height": HEIGHT, "pixel_format": "gray"},
        "method": {
            "model": "frame N approximated by alpha*N-1 + (1-alpha)*N+1",
            "residual_ratio_limit": RESIDUAL_RATIO_LIMIT,
            "minimum_neighbor_mae": MIN_MAE,
            "accepted_alpha_range": [0.05, 0.95],
        },
        "summary": {
            "tested_frame_count": len(rows),
            "candidate_count": len(findings),
        },
        "outputs": {
            "metrics": "blending/metrics.csv",
            "findings": "blending/findings.json",
        },
    }
    atomic_write_json(output_dir / "blending" / "blending.json", result)
    return result

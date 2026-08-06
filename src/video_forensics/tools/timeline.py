from __future__ import annotations

import csv
import json
from fractions import Fraction
from pathlib import Path
from time import monotonic
from typing import Any

from video_forensics.manifest import atomic_write_json, utc_now
from video_forensics.process import run_command

FFPROBE = Path("/usr/bin/ffprobe")


def _number(value: object) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _rate(value: object) -> float | None:
    if value in (None, "", "N/A", "0/0"):
        return None
    try:
        rate = Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        return None
    return float(rate) if rate > 0 else None


def _run_probe(video: Path, timeout: int) -> tuple[dict[str, Any], dict[str, object]]:
    entries = (
        "stream=index,time_base,avg_frame_rate,r_frame_rate,start_time,duration,nb_frames:"
        "frame=media_type,stream_index,key_frame,pict_type,pts,best_effort_timestamp,"
        "pkt_dts,pts_time,best_effort_timestamp_time,pkt_dts_time,pkt_duration,"
        "pkt_duration_time,pkt_pos,pkt_size"
    )

    argv = [
        str(FFPROBE),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_streams",
        "-show_frames",
        "-show_entries",
        entries,
        "-print_format",
        "json",
        str(video),
    ]

    result = run_command(argv, timeout=timeout)
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise RuntimeError(
            f"ffprobe timeline failed ({result.returncode}): {diagnostic}"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"ffprobe timeline returned invalid JSON: {exc}"
        ) from exc

    return payload, result.to_dict()


def _normalize_frames(payload: dict[str, Any]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for number, frame in enumerate(payload.get("frames", []), start=1):
        if frame.get("media_type") not in (None, "video"):
            continue
        normalized.append(
            {
                "frame_number": number,
                "stream_index": frame.get("stream_index"),
                "key_frame": frame.get("key_frame"),
                "pict_type": frame.get("pict_type"),
                "pts": frame.get("pts"),
                "pts_time": _number(frame.get("pts_time")),
                "best_effort_timestamp": frame.get("best_effort_timestamp"),
                "best_effort_timestamp_time": _number(
                    frame.get("best_effort_timestamp_time")
                ),
                "pkt_dts": frame.get("pkt_dts"),
                "pkt_dts_time": _number(frame.get("pkt_dts_time")),
                "pkt_duration": frame.get("pkt_duration"),
                "pkt_duration_time": _number(frame.get("pkt_duration_time")),
                "pkt_pos": frame.get("pkt_pos"),
                "pkt_size": frame.get("pkt_size"),
            }
        )
    return normalized


def _anomalies(frames: list[dict[str, object]]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    previous_pts: float | None = None
    previous_best: float | None = None

    for frame in frames:
        frame_number = int(frame["frame_number"])
        pts = frame["pts_time"]
        best = frame["best_effort_timestamp_time"]

        if pts is None:
            findings.append({"kind": "missing_pts_time", "frame_number": frame_number})
        elif previous_pts is not None:
            delta = float(pts) - previous_pts
            if delta < 0:
                findings.append(
                    {
                        "kind": "non_monotonic_pts",
                        "frame_number": frame_number,
                        "previous_pts_time": previous_pts,
                        "pts_time": pts,
                        "delta_seconds": delta,
                    }
                )
            elif delta == 0:
                findings.append(
                    {"kind": "duplicate_pts", "frame_number": frame_number, "pts_time": pts}
                )
        if pts is not None:
            previous_pts = float(pts)

        if best is not None and previous_best is not None:
            delta = float(best) - previous_best
            if delta <= 0:
                findings.append(
                    {
                        "kind": "non_increasing_best_effort_timestamp",
                        "frame_number": frame_number,
                        "previous_time": previous_best,
                        "time": best,
                        "delta_seconds": delta,
                    }
                )
        if best is not None:
            previous_best = float(best)

        duration = frame["pkt_duration_time"]
        if duration is not None and float(duration) < 0:
            findings.append(
                {
                    "kind": "negative_packet_duration",
                    "frame_number": frame_number,
                    "duration_seconds": duration,
                }
            )
    return findings


def _write_csv(path: Path, frames: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(frames[0]) if frames else ["frame_number"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(frames)


def analyze(video: Path, output_dir: Path, *, timeout: int = 3600) -> dict[str, object]:
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError(f"input is not a regular file: {video}")
    if not FFPROBE.is_file():
        raise FileNotFoundError(f"required executable not found: {FFPROBE}")

    started = monotonic()
    payload, command = _run_probe(video, timeout)
    frames = _normalize_frames(payload)
    findings = _anomalies(frames)
    streams = payload.get("streams", [])
    stream = streams[0] if streams else {}

    raw_path = output_dir / "timeline" / "raw_ffprobe.json"
    atomic_write_json(raw_path, payload)
    _write_csv(output_dir / "timeline" / "frames.csv", frames)
    atomic_write_json(output_dir / "timeline" / "anomalies.json", findings)

    durations = [
        float(frame["pkt_duration_time"])
        for frame in frames
        if frame["pkt_duration_time"] is not None
    ]
    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "timeline",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "tool": {"name": "ffprobe", "executable": str(FFPROBE)},
        "command": command,
        "stream": {
            "index": stream.get("index"),
            "time_base": stream.get("time_base"),
            "avg_frame_rate": stream.get("avg_frame_rate"),
            "avg_frame_rate_value": _rate(stream.get("avg_frame_rate")),
            "r_frame_rate": stream.get("r_frame_rate"),
            "r_frame_rate_value": _rate(stream.get("r_frame_rate")),
            "start_time": _number(stream.get("start_time")),
            "duration": _number(stream.get("duration")),
            "declared_frame_count": stream.get("nb_frames"),
        },
        "summary": {
            "decoded_frame_count": len(frames),
            "anomaly_count": len(findings),
            "first_pts_time": frames[0]["pts_time"] if frames else None,
            "last_pts_time": frames[-1]["pts_time"] if frames else None,
            "packet_duration_min": min(durations) if durations else None,
            "packet_duration_max": max(durations) if durations else None,
            "variable_packet_duration": len(set(durations)) > 1,
        },
        "outputs": {
            "raw_ffprobe": "timeline/raw_ffprobe.json",
            "frames": "timeline/frames.csv",
            "anomalies": "timeline/anomalies.json",
        },
    }
    atomic_write_json(output_dir / "timeline" / "timeline.json", result)
    return result

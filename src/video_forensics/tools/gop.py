from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from time import monotonic
from typing import Any

from video_forensics.manifest import atomic_write_json, utc_now
from video_forensics.process import run_command

FFPROBE = Path("/usr/bin/ffprobe")


def _run_probe(video: Path, timeout: int) -> tuple[dict[str, Any], dict[str, object]]:
    entries = (
        "frame=media_type,stream_index,key_frame,pict_type,pts_time,"
        "best_effort_timestamp_time,pkt_pos,pkt_size,coded_picture_number"
    )
    argv = [
        str(FFPROBE),
        "-v",
        "error",
        "-select_streams",
        "v:0",
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
        raise RuntimeError(f"ffprobe GOP analysis failed ({result.returncode}): {diagnostic}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe GOP analysis returned invalid JSON: {exc}") from exc
    return payload, result.to_dict()


def _float_or_none(value: object) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _int_or_none(value: object) -> int | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def _normalize_frames(payload: dict[str, Any]) -> list[dict[str, object]]:
    frames: list[dict[str, object]] = []
    for source in payload.get("frames", []):
        if source.get("media_type") not in (None, "video"):
            continue
        frames.append(
            {
                "frame_number": len(frames) + 1,
                "stream_index": _int_or_none(source.get("stream_index")),
                "key_frame": _int_or_none(source.get("key_frame")),
                "pict_type": source.get("pict_type"),
                "pts_time": _float_or_none(source.get("pts_time")),
                "best_effort_timestamp_time": _float_or_none(
                    source.get("best_effort_timestamp_time")
                ),
                "pkt_pos": _int_or_none(source.get("pkt_pos")),
                "pkt_size": _int_or_none(source.get("pkt_size")),
                "coded_picture_number": _int_or_none(source.get("coded_picture_number")),
            }
        )
    return frames


def _build_gops(frames: list[dict[str, object]]) -> list[dict[str, object]]:
    key_indexes = [index for index, frame in enumerate(frames) if frame["key_frame"] == 1]
    gops: list[dict[str, object]] = []
    for sequence, start_index in enumerate(key_indexes, start=1):
        end_index = (
            key_indexes[sequence] - 1 if sequence < len(key_indexes) else len(frames) - 1
        )
        members = frames[start_index : end_index + 1]
        start_time = members[0]["best_effort_timestamp_time"] if members else None
        end_time = members[-1]["best_effort_timestamp_time"] if members else None
        duration = None
        if start_time is not None and end_time is not None:
            duration = round(float(end_time) - float(start_time), 9)
        gops.append(
            {
                "gop_number": sequence,
                "start_frame": start_index + 1,
                "end_frame": end_index + 1,
                "length_frames": len(members),
                "start_time": start_time,
                "end_time": end_time,
                "span_seconds": duration,
                "picture_types": "".join(str(frame["pict_type"] or "?") for frame in members),
                "packet_bytes": sum(int(frame["pkt_size"] or 0) for frame in members),
            }
        )
    return gops


def _findings(
    frames: list[dict[str, object]], gops: list[dict[str, object]]
) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    if frames and not gops:
        findings.append({"kind": "no_key_frames_reported"})
    if gops and int(gops[0]["start_frame"]) != 1:
        findings.append(
            {
                "kind": "frames_before_first_key_frame",
                "frame_count": int(gops[0]["start_frame"]) - 1,
            }
        )
    for frame in frames:
        if frame["key_frame"] == 1 and frame["pict_type"] not in ("I", None):
            findings.append(
                {
                    "kind": "key_frame_not_i_picture",
                    "frame_number": frame["frame_number"],
                    "pict_type": frame["pict_type"],
                }
            )
        if frame["pict_type"] is None:
            findings.append(
                {"kind": "missing_picture_type", "frame_number": frame["frame_number"]}
            )
    return findings


def _write_csv(path: Path, rows: list[dict[str, object]], default_columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0]) if rows else default_columns
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def analyze(video: Path, output_dir: Path, *, timeout: int = 3600) -> dict[str, object]:
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError(f"input is not a regular file: {video}")
    if not FFPROBE.is_file():
        raise FileNotFoundError(f"required executable not found: {FFPROBE}")

    started = monotonic()
    payload, command = _run_probe(video, timeout)
    frames = _normalize_frames(payload)
    gops = _build_gops(frames)
    findings = _findings(frames, gops)
    picture_types = Counter(str(frame["pict_type"] or "unknown") for frame in frames)
    gop_lengths = [int(gop["length_frames"]) for gop in gops]

    atomic_write_json(output_dir / "gop" / "raw_ffprobe.json", payload)
    _write_csv(output_dir / "gop" / "frames.csv", frames, ["frame_number"])
    _write_csv(output_dir / "gop" / "gops.csv", gops, ["gop_number"])
    atomic_write_json(output_dir / "gop" / "findings.json", findings)

    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "gop",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "tool": {"name": "ffprobe", "executable": str(FFPROBE)},
        "command": command,
        "summary": {
            "frame_count": len(frames),
            "key_frame_count": len(gops),
            "gop_count": len(gops),
            "picture_type_counts": dict(sorted(picture_types.items())),
            "gop_length_min": min(gop_lengths) if gop_lengths else None,
            "gop_length_max": max(gop_lengths) if gop_lengths else None,
            "distinct_gop_lengths": sorted(set(gop_lengths)),
            "finding_count": len(findings),
        },
        "outputs": {
            "raw_ffprobe": "gop/raw_ffprobe.json",
            "frames": "gop/frames.csv",
            "gops": "gop/gops.csv",
            "findings": "gop/findings.json",
        },
    }
    atomic_write_json(output_dir / "gop" / "gop.json", result)
    return result

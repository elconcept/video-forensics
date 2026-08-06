from __future__ import annotations

import struct
from pathlib import Path
from time import monotonic
from typing import BinaryIO

from video_forensics.manifest import atomic_write_json, utc_now

ISO_BMFF_SUFFIXES = {".3g2", ".3gp", ".m4v", ".mov", ".mp4"}
CONTAINER_TYPES = {
    b"dinf",
    b"edts",
    b"gmhd",
    b"ilst",
    b"mdia",
    b"meta",
    b"mfra",
    b"minf",
    b"moof",
    b"moov",
    b"mvex",
    b"schi",
    b"sinf",
    b"skip",
    b"stbl",
    b"traf",
    b"trak",
    b"udta",
}
FULL_BOX_CONTAINERS = {b"meta"}
MAX_DEPTH = 32


def _type_name(value: bytes) -> str:
    return value.decode("latin-1", errors="replace")


def _read_header(handle: BinaryIO, offset: int, boundary: int) -> tuple[int, bytes, int] | None:
    if boundary - offset < 8:
        return None
    handle.seek(offset)
    header = handle.read(8)
    if len(header) != 8:
        return None

    size32, atom_type = struct.unpack(">I4s", header)
    header_size = 8
    if size32 == 1:
        extended = handle.read(8)
        if len(extended) != 8:
            return None
        size = struct.unpack(">Q", extended)[0]
        header_size = 16
    elif size32 == 0:
        size = boundary - offset
    else:
        size = size32
    return size, atom_type, header_size


def _walk(
    handle: BinaryIO,
    start: int,
    end: int,
    *,
    depth: int,
    atoms: list[dict[str, object]],
    anomalies: list[dict[str, object]],
) -> None:
    if depth > MAX_DEPTH:
        anomalies.append({"kind": "maximum_depth_exceeded", "offset": start, "depth": depth})
        return

    offset = start
    while offset < end:
        remaining = end - offset
        if remaining < 8:
            anomalies.append(
                {"kind": "trailing_bytes", "offset": offset, "size": remaining, "depth": depth}
            )
            return

        parsed = _read_header(handle, offset, end)
        if parsed is None:
            anomalies.append({"kind": "truncated_header", "offset": offset, "depth": depth})
            return
        size, atom_type, header_size = parsed
        atom_name = _type_name(atom_type)

        if size < header_size:
            anomalies.append(
                {
                    "kind": "invalid_atom_size",
                    "type": atom_name,
                    "offset": offset,
                    "size": size,
                    "header_size": header_size,
                    "depth": depth,
                }
            )
            return
        if offset + size > end:
            anomalies.append(
                {
                    "kind": "atom_exceeds_boundary",
                    "type": atom_name,
                    "offset": offset,
                    "size": size,
                    "boundary": end,
                    "depth": depth,
                }
            )
            return

        body_offset = offset + header_size
        body_size = size - header_size
        atom = {
            "type": atom_name,
            "offset": offset,
            "size": size,
            "header_size": header_size,
            "body_offset": body_offset,
            "body_size": body_size,
            "depth": depth,
            "parent_end": end,
        }
        atoms.append(atom)

        if atom_type in CONTAINER_TYPES and body_size:
            child_start = body_offset + (4 if atom_type in FULL_BOX_CONTAINERS else 0)
            if child_start > offset + size:
                anomalies.append(
                    {"kind": "invalid_container_payload", "type": atom_name, "offset": offset}
                )
            elif child_start < offset + size:
                _walk(
                    handle,
                    child_start,
                    offset + size,
                    depth=depth + 1,
                    atoms=atoms,
                    anomalies=anomalies,
                )
        offset += size


def analyze(video: Path, output_dir: Path) -> dict[str, object]:
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError(f"input is not a regular file: {video}")

    started = monotonic()
    file_size = video.stat().st_size
    atoms: list[dict[str, object]] = []
    anomalies: list[dict[str, object]] = []
    applicability = "applicable" if video.suffix.lower() in ISO_BMFF_SUFFIXES else "unknown"

    with video.open("rb", buffering=0) as handle:
        _walk(handle, 0, file_size, depth=0, atoms=atoms, anomalies=anomalies)

    top_level = [atom for atom in atoms if atom["depth"] == 0]
    type_counts: dict[str, int] = {}
    for atom in atoms:
        atom_type = str(atom["type"])
        type_counts[atom_type] = type_counts.get(atom_type, 0) + 1

    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "container_structure",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "applicability": applicability,
        "input_size_bytes": file_size,
        "summary": {
            "atom_count": len(atoms),
            "top_level_atom_count": len(top_level),
            "anomaly_count": len(anomalies),
            "type_counts": dict(sorted(type_counts.items())),
            "top_level_order": [str(atom["type"]) for atom in top_level],
        },
        "atoms": atoms,
        "anomalies": anomalies,
    }
    atomic_write_json(output_dir / "container" / "structure.json", result)
    return result

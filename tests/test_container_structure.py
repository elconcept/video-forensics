from __future__ import annotations

import json
import struct
from pathlib import Path

from video_forensics.tools.container_structure import analyze


def atom(kind: bytes, payload: bytes = b"") -> bytes:
    return struct.pack(">I4s", 8 + len(payload), kind) + payload


def test_parses_nested_iso_bmff_atoms(tmp_path: Path) -> None:
    video = tmp_path / "sample.mp4"
    output = tmp_path / "results"
    ftyp = atom(b"ftyp", b"isom\x00\x00\x00\x00isom")
    trak = atom(b"trak", atom(b"mdia", atom(b"hdlr", b"data")))
    moov = atom(b"moov", trak)
    mdat = atom(b"mdat", b"video-data")
    video.write_bytes(ftyp + moov + mdat)

    result = analyze(video, output)

    assert result["summary"]["top_level_order"] == ["ftyp", "moov", "mdat"]
    assert result["summary"]["type_counts"]["trak"] == 1
    assert result["summary"]["type_counts"]["mdia"] == 1
    assert result["summary"]["anomaly_count"] == 0
    saved = json.loads((output / "container" / "structure.json").read_text())
    assert saved["summary"]["atom_count"] == 6


def test_reports_atom_exceeding_file_boundary(tmp_path: Path) -> None:
    video = tmp_path / "broken.mp4"
    output = tmp_path / "results"
    video.write_bytes(struct.pack(">I4s", 100, b"mdat") + b"short")

    result = analyze(video, output)

    assert result["summary"]["atom_count"] == 0
    assert result["anomalies"][0]["kind"] == "atom_exceeds_boundary"


def test_supports_extended_size_atom(tmp_path: Path) -> None:
    video = tmp_path / "extended.mov"
    output = tmp_path / "results"
    payload = b"12345678"
    video.write_bytes(struct.pack(">I4sQ", 1, b"free", 16 + len(payload)) + payload)

    result = analyze(video, output)

    assert result["atoms"][0]["header_size"] == 16
    assert result["atoms"][0]["size"] == 24

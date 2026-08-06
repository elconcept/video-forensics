from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from video_forensics.native.orphan_stream_builder import build, parse_nal_units


def nal(nal_type: int, payload: bytes) -> bytes:
    return b"\x00\x00\x00\x01" + bytes(((nal_type << 1) & 0x7E, 1)) + payload

def approved_plan(stream: Path, payload: dict[str, object]) -> dict[str, object]:
    return {
        "status": "approved_for_controlled_reconstruction",
        "source": {
            "path": str(stream),
            "size_bytes": stream.stat().st_size,
            "sha256": hashlib.sha256(stream.read_bytes()).hexdigest(),
        },
        **payload,
    }

def test_builds_byte_exact_variants(tmp_path: Path) -> None:
    units = [
        nal(32, b"vps"),
        nal(33, b"sps"),
        nal(34, b"pps"),
        nal(19, b"idr-a"),
        nal(19, b"idr-b"),
        nal(1, b"tail-1"),
        nal(1, b"tail-2"),
    ]
    stream = tmp_path / "source.h265"
    stream.write_bytes(b"".join(units))
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            approved_plan(
                stream,
                {
                    "parameter_nals": [1, 2, 3],
                    "reference_idr_nals": [4, 5],
                    "orphan_start_nal": 6,
                    "orphan_end_nal": 7,
                },
            )
        ),
        encoding="utf-8",
    )

    result = build(stream, plan, tmp_path / "output")

    assert len(result["variants"]) == 2
    assert (
        tmp_path / "output" / "orphan_ref_nal_000004.h265"
    ).read_bytes() == b"".join(
        [units[0], units[1], units[2], units[3], units[5], units[6]]
    )
    assert parse_nal_units(stream)[-1]["nal_unit_type"] == 1

def test_rejects_non_idr_reference(tmp_path: Path) -> None:
    stream = tmp_path / "source.h265"
    stream.write_bytes(
        nal(32, b"v") + nal(33, b"s") + nal(34, b"p") + nal(1, b"tail")
    )
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            approved_plan(
                stream,
                {
                    "parameter_nals": [1, 2, 3],
                    "reference_idr_nals": [4],
                    "orphan_start_nal": 4,
                    "orphan_end_nal": 4,
                },
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-IDR"):
        build(stream, plan, tmp_path / "output")
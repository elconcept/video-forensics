from __future__ import annotations

from pathlib import Path

import pytest

from video_forensics.native.libde265_run import frame_inventory, frame_size, run_decode


def test_frame_size_yuv420p() -> None:
    assert frame_size(1920, 1080, "yuv420p") == 3_110_400
    with pytest.raises(ValueError, match="even"):
        frame_size(1919, 1080, "yuv420p")


def test_frame_inventory_hashes_each_frame(tmp_path: Path) -> None:
    yuv = tmp_path / "decoded.yuv"
    yuv.write_bytes(b"abcd" + b"efgh")
    rows = frame_inventory(yuv, 4)
    assert len(rows) == 2
    assert rows[1]["offset"] == 4


def test_missing_decoder_degrades_gracefully(tmp_path: Path) -> None:
    source = tmp_path / "source.h265"
    source.write_bytes(b"stream")
    result = run_decode(
        source,
        tmp_path / "output",
        binary=None,
        width=1920,
        height=1080,
        pixel_format="yuv420p",
        threads=0,
        host_profile_id="host",
        timeout=60,
    )
    assert result["status"] == "unavailable"

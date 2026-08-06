from __future__ import annotations

import pytest

from video_forensics.tools.hevc_poc import SPS, BitReader
from video_forensics.tools.hevc_slice_address import (
    address_coordinates,
    ceil_log2,
    derive_ctb_geometry,
    read_slice_segment_address,
)


def test_ceil_log2_uses_exact_integer_arithmetic() -> None:
    assert ceil_log2(1) == 0
    assert ceil_log2(2) == 1
    assert ceil_log2(3) == 2
    assert ceil_log2(510) == 9
    assert ceil_log2(512) == 9
    assert ceil_log2(513) == 10


def test_geometry_uses_coded_luma_dimensions_and_ctb_size() -> None:
    sps = SPS(0, 1920, 1088, 8, 0, 6)
    geometry = derive_ctb_geometry(sps)
    assert geometry.ctb_size_y == 64
    assert geometry.pic_width_in_ctbs_y == 30
    assert geometry.pic_height_in_ctbs_y == 17
    assert geometry.pic_size_in_ctbs_y == 510
    assert geometry.address_bit_count == 9
    assert address_coordinates(509, geometry) == (29, 16)


def test_address_is_read_as_fixed_width_unsigned_value() -> None:
    sps = SPS(0, 1920, 1088, 8, 0, 6)
    geometry = derive_ctb_geometry(sps)
    reader = BitReader(bytes((0b10101010, 0b10000000)))
    assert read_slice_segment_address(reader, geometry) == 341
    assert reader.position == 9


def test_rejects_code_points_outside_picture_size() -> None:
    sps = SPS(0, 1920, 1088, 8, 0, 6)
    geometry = derive_ctb_geometry(sps)
    reader = BitReader(bytes((0xFF, 0x80)))
    with pytest.raises(ValueError, match="outside PicSizeInCtbsY"):
        read_slice_segment_address(reader, geometry)

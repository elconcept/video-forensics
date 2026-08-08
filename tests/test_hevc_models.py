from __future__ import annotations

from video_forensics.tools import hevc_poc
from video_forensics.tools.hevc_models import BitReader, PPS, SPS


def test_hevc_poc_reexports_neutral_models() -> None:
    assert hevc_poc.BitReader is BitReader
    assert hevc_poc.SPS is SPS
    assert hevc_poc.PPS is PPS


def test_bit_reader_remains_operational() -> None:
    reader = BitReader(bytes([0b10100000]))
    assert reader.bit() == 1
    assert reader.bits(2) == 1

from __future__ import annotations

from video_forensics.tools.hevc_sps import (
    BitReader,
    parse_short_term_rps,
    remove_emulation_prevention,
)


def bits_to_bytes(bits: str) -> bytes:
    padded = bits + "0" * ((8 - len(bits) % 8) % 8)
    return int(padded, 2).to_bytes(len(padded) // 8, "big")


def ue(value: int) -> str:
    code_num = value + 1
    payload = f"{code_num:b}"
    return "0" * (len(payload) - 1) + payload


def test_remove_emulation_prevention() -> None:
    assert remove_emulation_prevention(b"\x00\x00\x03\x01") == b"\x00\x00\x01"


def test_bit_reader_signed_exp_golomb() -> None:
    reader = BitReader(bits_to_bytes(ue(1) + ue(2)))
    assert reader.se() == 1
    assert reader.se() == -1


def test_explicit_short_term_rps() -> None:
    syntax = ue(1) + ue(1) + ue(0) + "1" + ue(1) + "0"
    result = parse_short_term_rps(BitReader(bits_to_bytes(syntax)), 0, [])
    assert result["num_negative_pics"] == 1
    assert result["num_positive_pics"] == 1
    assert result["delta_poc"] == [-1, 2]
    assert result["used_by_curr_pic_flags"] == [1, 0]

from __future__ import annotations

from dataclasses import dataclass

class BitReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.position = 0

    def bit(self) -> int:
        if self.position >= len(self.data) * 8:
            raise ValueError("unexpected end of RBSP")
        byte = self.data[self.position // 8]
        value = (byte >> (7 - self.position % 8)) & 1
        self.position += 1
        return value

    def bits(self, count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | self.bit()
        return value

    def ue(self) -> int:
        leading_zero_bits = 0
        while self.bit() == 0:
            leading_zero_bits += 1
            if leading_zero_bits > 31:
                raise ValueError("Exp-Golomb value is too large")
        suffix = self.bits(leading_zero_bits) if leading_zero_bits else 0
        return (1 << leading_zero_bits) - 1 + suffix

    def ue_signed(self) -> int:
        code_num = self.ue()
        magnitude = (code_num + 1) // 2
        return magnitude if code_num % 2 else -magnitude

class SPS:
    sps_id: int
    width: int
    height: int
    log2_max_poc_lsb: int
    separate_colour_plane_flag: int
    log2_ctb_size: int
    long_term_ref_pics_present_flag: int = 0

class PPS:
    pps_id: int
    sps_id: int
    dependent_slice_segments_enabled_flag: int
    output_flag_present_flag: int
    num_extra_slice_header_bits: int

from __future__ import annotations

from video_forensics.tools.hevc_poc import derive_poc, rbsp


def test_rbsp_removes_emulation_prevention_byte() -> None:
    assert rbsp(b"\x00\x00\x03\x01") == b"\x00\x00\x01"


def test_poc_regression_without_wrap() -> None:
    poc, msb = derive_poc(1, 50, 0, 7)
    assert poc == 1
    assert msb == 0


def test_poc_wrap_forward() -> None:
    poc, msb = derive_poc(2, 126, 0, 7)
    assert poc == 130
    assert msb == 128

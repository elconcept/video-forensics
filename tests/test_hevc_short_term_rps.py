from __future__ import annotations

from video_forensics.tools.hevc_poc import BitReader
from video_forensics.tools.hevc_short_term_rps import parse_short_term_rps


def bits(data: str) -> BitReader:
    padded = data + "0" * ((8 - len(data) % 8) % 8)
    return BitReader(
        bytes(int(padded[index : index + 8], 2) for index in range(0, len(padded), 8))
    )


def test_explicit_short_term_rps() -> None:
    # num_negative=2 ue(2)=011, num_positive=1 ue(1)=010
    # negative deltas: -(0+1) used, then -(1+1) unused -> -1, -3
    # positive delta: +(2+1) used -> +3
    reader = bits("011010" "1" "1" "010" "0" "011" "1")
    parsed = parse_short_term_rps(
        reader, 0, 1, [], from_slice_header=False
    )
    assert parsed.negative_delta_pocs == (-1, -3)
    assert parsed.positive_delta_pocs == (3,)
    assert parsed.used_by_curr_pic_s0 == (1, 0)
    assert parsed.used_by_curr_pic_s1 == (1,)


def test_predicted_short_term_rps_from_slice_header() -> None:
    reference = parse_short_term_rps(
        bits("010010" "1" "1" "1" "1"),
        0,
        1,
        [],
        from_slice_header=False,
    )
    # predicted=1, delta_idx_minus1=0, sign=0, abs_delta_minus1=0 => +1
    # reference entries -1,+1,0: include all and mark first/third used
    reader = bits("1" "1" "0" "1" "1" "0" "1" "1")
    parsed = parse_short_term_rps(
        reader,
        1,
        1,
        [reference],
        from_slice_header=True,
    )
    assert parsed.inter_ref_pic_set_prediction_flag == 1
    assert parsed.reference_index == 0
    assert parsed.delta_rps == 1
    assert parsed.positive_delta_pocs == (1, 2)

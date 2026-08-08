from __future__ import annotations

from dataclasses import asdict, dataclass

from video_forensics.tools.hevc_models import BitReader
from video_forensics.tools.hevc_poc import rbsp, skip_profile_tier_level

MAX_SHORT_TERM_REFS = 16


@dataclass(frozen=True)
class ShortTermRPS:
    index: int
    inter_ref_pic_set_prediction_flag: int
    delta_idx_minus1: int | None
    reference_index: int | None
    delta_rps_sign: int | None
    abs_delta_rps_minus1: int | None
    delta_rps: int | None
    negative_delta_pocs: tuple[int, ...]
    positive_delta_pocs: tuple[int, ...]
    used_by_curr_pic_s0: tuple[int, ...]
    used_by_curr_pic_s1: tuple[int, ...]
    num_negative_pics: int
    num_positive_pics: int
    num_delta_pocs: int
    syntax_bits: int

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        for key in (
            "negative_delta_pocs",
            "positive_delta_pocs",
            "used_by_curr_pic_s0",
            "used_by_curr_pic_s1",
        ):
            value[key] = list(value[key])
        return value


def skip_scaling_list_data(reader: BitReader) -> None:
    for size_id in range(4):
        matrix_id = 0
        step = 3 if size_id == 3 else 1
        while matrix_id < 6:
            prediction_mode = reader.bit()
            if not prediction_mode:
                reader.ue()
            else:
                coefficient_count = min(64, 1 << (4 + (size_id << 1)))
                if size_id > 1:
                    reader.ue_signed()
                for _ in range(coefficient_count):
                    reader.ue_signed()
            matrix_id += step


def _validate_count(count: int) -> None:
    if count > MAX_SHORT_TERM_REFS:
        raise ValueError(
            f"short-term RPS contains {count} entries; maximum is {MAX_SHORT_TERM_REFS}"
        )


def parse_short_term_rps(
    reader: BitReader,
    index: int,
    num_short_term_ref_pic_sets: int,
    previous_sets: list[ShortTermRPS],
    *,
    from_slice_header: bool,
) -> ShortTermRPS:
    started = reader.position
    predicted = reader.bit() if index != 0 else 0
    if not predicted:
        num_negative = reader.ue()
        num_positive = reader.ue()
        _validate_count(num_negative + num_positive)
        negatives: list[int] = []
        positives: list[int] = []
        used_negative: list[int] = []
        used_positive: list[int] = []
        delta = 0
        for _ in range(num_negative):
            delta -= reader.ue() + 1
            negatives.append(delta)
            used_negative.append(reader.bit())
        delta = 0
        for _ in range(num_positive):
            delta += reader.ue() + 1
            positives.append(delta)
            used_positive.append(reader.bit())
        return ShortTermRPS(
            index=index,
            inter_ref_pic_set_prediction_flag=0,
            delta_idx_minus1=None,
            reference_index=None,
            delta_rps_sign=None,
            abs_delta_rps_minus1=None,
            delta_rps=None,
            negative_delta_pocs=tuple(negatives),
            positive_delta_pocs=tuple(positives),
            used_by_curr_pic_s0=tuple(used_negative),
            used_by_curr_pic_s1=tuple(used_positive),
            num_negative_pics=num_negative,
            num_positive_pics=num_positive,
            num_delta_pocs=num_negative + num_positive,
            syntax_bits=reader.position - started,
        )

    delta_idx_minus1 = reader.ue() if from_slice_header else 0
    reference_index = index - (delta_idx_minus1 + 1)
    if reference_index < 0 or reference_index >= len(previous_sets):
        raise ValueError(
            f"short-term RPS reference index outside available sets: {reference_index}"
        )
    reference = previous_sets[reference_index]
    delta_rps_sign = reader.bit()
    abs_delta_rps_minus1 = reader.ue()
    delta_rps = (-1 if delta_rps_sign else 1) * (abs_delta_rps_minus1 + 1)
    reference_deltas = [
        *reference.negative_delta_pocs,
        *reference.positive_delta_pocs,
        0,
    ]
    reference_used = [
        *reference.used_by_curr_pic_s0,
        *reference.used_by_curr_pic_s1,
        1,
    ]
    candidates: list[tuple[int, int]] = []
    for delta_poc, inherited_used in zip(
        reference_deltas, reference_used, strict=True
    ):
        used = reader.bit()
        use_delta = 1 if used else reader.bit()
        candidate = delta_poc + delta_rps
        if use_delta and candidate != 0:
            candidates.append((candidate, used or inherited_used and used))
    negatives = sorted(
        ((delta, used) for delta, used in candidates if delta < 0),
        key=lambda item: item[0],
        reverse=True,
    )
    positives = sorted(
        ((delta, used) for delta, used in candidates if delta > 0),
        key=lambda item: item[0],
    )
    _validate_count(len(negatives) + len(positives))
    return ShortTermRPS(
        index=index,
        inter_ref_pic_set_prediction_flag=1,
        delta_idx_minus1=delta_idx_minus1,
        reference_index=reference_index,
        delta_rps_sign=delta_rps_sign,
        abs_delta_rps_minus1=abs_delta_rps_minus1,
        delta_rps=delta_rps,
        negative_delta_pocs=tuple(delta for delta, _ in negatives),
        positive_delta_pocs=tuple(delta for delta, _ in positives),
        used_by_curr_pic_s0=tuple(used for _, used in negatives),
        used_by_curr_pic_s1=tuple(used for _, used in positives),
        num_negative_pics=len(negatives),
        num_positive_pics=len(positives),
        num_delta_pocs=len(negatives) + len(positives),
        syntax_bits=reader.position - started,
    )


def parse_sps_short_term_rps(nal_payload: bytes) -> dict[str, object]:
    reader = BitReader(rbsp(nal_payload[2:]))
    reader.bits(4)
    max_sub_layers_minus1 = reader.bits(3)
    reader.bit()
    skip_profile_tier_level(reader, max_sub_layers_minus1)
    sps_id = reader.ue()
    chroma_format_idc = reader.ue()
    if chroma_format_idc == 3:
        reader.bit()
    reader.ue()
    reader.ue()
    if reader.bit():
        for _ in range(4):
            reader.ue()
    reader.ue()
    reader.ue()
    reader.ue()
    sub_layer_ordering_info_present_flag = reader.bit()
    first_layer = 0 if sub_layer_ordering_info_present_flag else max_sub_layers_minus1
    for _ in range(first_layer, max_sub_layers_minus1 + 1):
        reader.ue()
        reader.ue()
        reader.ue()
    reader.ue()
    reader.ue()
    reader.ue()
    reader.ue()
    reader.ue()
    reader.ue()
    scaling_list_enabled = reader.bit()
    if scaling_list_enabled and reader.bit():
        skip_scaling_list_data(reader)
    reader.bit()
    reader.bit()
    if reader.bit():
        reader.bits(4)
        reader.bits(4)
        reader.ue()
        reader.ue()
        reader.bit()
    count = reader.ue()
    if count > 64:
        raise ValueError(f"num_short_term_ref_pic_sets too large: {count}")
    sets: list[ShortTermRPS] = []
    for index in range(count):
        sets.append(
            parse_short_term_rps(
                reader,
                index,
                count,
                sets,
                from_slice_header=False,
            )
        )
    return {
        "sps_id": sps_id,
        "num_short_term_ref_pic_sets": count,
        "sets": [item.to_dict() for item in sets],
        "parsed_sets": sets,
        "bits_consumed_through_rps": reader.position,
    }

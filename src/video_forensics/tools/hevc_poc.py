from __future__ import annotations

from dataclasses import dataclass

from video_forensics.tools.hevc_pps import parse_pps_complete, pps_to_dict
from video_forensics.tools.hevc_sps import parse_sps_complete, sps_to_dict

IRAP_TYPES = set(range(16, 24))
IDR_TYPES = {19, 20}
VCL_TYPES = set(range(32))


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


def rbsp(payload: bytes) -> bytes:
    output = bytearray()
    zero_count = 0
    for value in payload:
        if zero_count >= 2 and value == 0x03:
            zero_count = 0
            continue
        output.append(value)
        zero_count = zero_count + 1 if value == 0 else 0
    return bytes(output)


def skip_profile_tier_level(reader: BitReader, max_sub_layers_minus1: int) -> None:
    reader.bits(2 + 1 + 5)
    reader.bits(32)
    reader.bits(4)
    reader.bits(44)
    reader.bits(8)
    profile_present = [reader.bit() for _ in range(max_sub_layers_minus1)]
    level_present = [reader.bit() for _ in range(max_sub_layers_minus1)]
    if max_sub_layers_minus1:
        for _ in range(max_sub_layers_minus1, 8):
            reader.bits(2)
    for index in range(max_sub_layers_minus1):
        if profile_present[index]:
            reader.bits(2 + 1 + 5)
            reader.bits(32)
            reader.bits(4)
            reader.bits(44)
        if level_present[index]:
            reader.bits(8)


@dataclass(frozen=True)
class SPS:
    sps_id: int
    width: int
    height: int
    log2_max_poc_lsb: int
    separate_colour_plane_flag: int


@dataclass(frozen=True)
class PPS:
    pps_id: int
    sps_id: int
    dependent_slice_segments_enabled_flag: int
    output_flag_present_flag: int
    num_extra_slice_header_bits: int


@dataclass(frozen=True)
class SliceHeader:
    first_slice_segment_in_pic_flag: int
    pps_id: int
    slice_type: int | None
    poc_lsb: int | None


def parse_sps(nal_payload: bytes):
    return parse_sps_complete(nal_payload)


def parse_pps(nal_payload: bytes):
    return parse_pps_complete(nal_payload)


def parse_first_slice(
    nal_payload: bytes,
    nal_type: int,
    pps_map: dict[int, PPS],
    sps_map: dict[int, SPS],
) -> SliceHeader:
    reader = BitReader(rbsp(nal_payload[2:]))
    first = reader.bit()
    if nal_type in IRAP_TYPES:
        reader.bit()
    pps_id = reader.ue()
    if not first:
        return SliceHeader(first, pps_id, None, None)
    pps = pps_map[pps_id]
    sps = sps_map[pps.sps_id]
    for _ in range(pps.num_extra_slice_header_bits):
        reader.bit()
    slice_type = reader.ue()
    if pps.output_flag_present_flag:
        reader.bit()
    if sps.separate_colour_plane_flag:
        reader.bits(2)
    poc_lsb = None if nal_type in IDR_TYPES else reader.bits(sps.log2_max_poc_lsb)
    return SliceHeader(first, pps_id, slice_type, poc_lsb)


def derive_poc(
    poc_lsb: int,
    previous_lsb: int,
    previous_msb: int,
    log2_max_poc_lsb: int,
) -> tuple[int, int]:
    maximum = 1 << log2_max_poc_lsb
    if poc_lsb < previous_lsb and previous_lsb - poc_lsb >= maximum // 2:
        poc_msb = previous_msb + maximum
    elif poc_lsb > previous_lsb and poc_lsb - previous_lsb > maximum // 2:
        poc_msb = previous_msb - maximum
    else:
        poc_msb = previous_msb
    return poc_msb + poc_lsb, poc_msb


def analyze_poc(nals: list[dict[str, object]]) -> dict[str, object]:
    sps_map: dict[int, SPS] = {}
    pps_map: dict[int, PPS] = {}
    parameter_nals: list[int] = []
    idr_nals: list[int] = []
    pictures: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    parse_errors: list[dict[str, object]] = []
    previous_lsb = 0
    previous_msb = 0
    previous_poc: int | None = None

    for nal in nals:
        nal_type = int(nal["nal_unit_type"])
        nal_number = int(nal["nal_number"])
        payload = bytes(nal["payload"])
        try:
            if nal_type == 33:
                parsed_sps = parse_sps(payload)
                sps_map[parsed_sps.sps_id] = parsed_sps
                parameter_nals.append(nal_number)
                continue
            if nal_type == 34:
                parsed_pps = parse_pps(payload)
                pps_map[parsed_pps.pps_id] = parsed_pps
                parameter_nals.append(nal_number)
                continue
            if nal_type == 32:
                parameter_nals.append(nal_number)
                continue
            if nal_type not in VCL_TYPES:
                continue
            header = parse_first_slice(payload, nal_type, pps_map, sps_map)
            if not header.first_slice_segment_in_pic_flag:
                continue
            if nal_type in IDR_TYPES:
                poc = 0
                poc_lsb = 0
                poc_msb = 0
                previous_lsb = 0
                previous_msb = 0
                idr_nals.append(nal_number)
            else:
                if header.poc_lsb is None:
                    raise ValueError("non-IDR first slice has no POC LSB")
                pps = pps_map[header.pps_id]
                sps = sps_map[pps.sps_id]
                poc, poc_msb = derive_poc(
                    header.poc_lsb,
                    previous_lsb,
                    previous_msb,
                    sps.log2_max_poc_lsb,
                )
                poc_lsb = header.poc_lsb
                previous_lsb = poc_lsb
                previous_msb = poc_msb
            picture = {
                "picture_number": len(pictures) + 1,
                "nal_number": nal_number,
                "offset": int(nal["offset"]),
                "nal_unit_type": nal_type,
                "is_irap": nal_type in IRAP_TYPES,
                "slice_type": header.slice_type,
                "pps_id": header.pps_id,
                "poc_lsb": poc_lsb,
                "poc_msb": poc_msb,
                "poc": poc,
            }
            if previous_poc is not None and poc < previous_poc and nal_type not in IRAP_TYPES:
                finding = {
                    "id": "HEVC_POC_REGRESSION_WITHOUT_IRAP",
                    "severity": "high",
                    "description": "Picture Order Count decreased at a non-IRAP picture.",
                    "evidence_refs": [
                        f"hevc_bitstream/pictures.csv#picture-{picture['picture_number']}"
                    ],
                    "requires_reference": False,
                    "host_profile": None,
                    "observations": {
                        "previous_poc": previous_poc,
                        "current_poc": poc,
                        "current_poc_lsb": poc_lsb,
                        "nal_number": nal_number,
                        "offset": int(nal["offset"]),
                        "nal_unit_type": nal_type,
                    },
                    "interpretation_boundary": (
                        "The regression identifies a coded-sequence discontinuity requiring "
                        "reference-picture and access-point analysis. It does not alone identify "
                        "the editing operation that produced the stream."
                    ),
                }
                findings.append(finding)
            pictures.append(picture)
            previous_poc = poc
        except (KeyError, ValueError) as exc:
            parse_errors.append(
                {
                    "nal_number": nal_number,
                    "offset": int(nal["offset"]),
                    "nal_unit_type": nal_type,
                    "error": str(exc),
                }
            )

    plan = None
    if findings and parameter_nals and idr_nals:
        first_regression_nal = int(findings[0]["observations"]["nal_number"])
        vcl_numbers = [
            int(nal["nal_number"])
            for nal in nals
            if int(nal["nal_unit_type"]) in VCL_TYPES
            and int(nal["nal_number"]) >= first_regression_nal
        ]
        if vcl_numbers:
            plan = {
                "parameter_nals": parameter_nals[-3:],
                "reference_idr_nals": idr_nals,
                "orphan_start_nal": first_regression_nal,
                "orphan_end_nal": max(vcl_numbers),
                "status": "draft_requires_review",
            }
    return {
        "sps": [sps_to_dict(value) for value in sps_map.values()],
        "pps": [pps_to_dict(value) for value in pps_map.values()],
        "pictures": pictures,
        "findings": findings,
        "parse_errors": parse_errors,
        "orphan_plan_draft": plan,
    }

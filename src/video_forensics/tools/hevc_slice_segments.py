from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from video_forensics.tools.hevc_poc import IRAP_TYPES, PPS, SPS, BitReader, rbsp


@dataclass(frozen=True)
class SliceSegmentHeader:
    nal_number: int
    nal_unit_type: int
    first_slice_segment_in_pic_flag: int
    no_output_of_prior_pics_flag: int | None
    pps_id: int
    dependent_slice_segment_flag: int
    slice_segment_address: int
    slice_segment_ctb_x: int
    slice_segment_ctb_y: int
    pic_width_in_ctbs_y: int
    pic_height_in_ctbs_y: int
    pic_size_in_ctbs_y: int
    slice_segment_address_bit_count: int
    inherited_from_nal_number: int | None
    slice_type: int | None
    pic_output_flag: int | None
    colour_plane_id: int | None
    poc_lsb: int | None
    header_bits_consumed: int
    header_bytes_covered: int
    parser_status: str



def parse_slice_segment_header(
    nal_payload: bytes,
    nal_type: int,
    nal_number: int,
    pps_map: dict[int, PPS],
    sps_map: dict[int, SPS],
    preceding_independent: SliceSegmentHeader | None,
) -> SliceSegmentHeader:
    reader = BitReader(rbsp(nal_payload[2:]))
    first = reader.bit()
    no_output = reader.bit() if nal_type in IRAP_TYPES else None
    pps_id = reader.ue()
    pps = pps_map[pps_id]
    sps = sps_map[pps.sps_id]

    geometry = derive_ctb_geometry(sps)
    dependent = 0
    address = 0
    if not first:
        if pps.dependent_slice_segments_enabled_flag:
            dependent = reader.bit()
        address = read_slice_segment_address(reader, geometry)
    ctb_x, ctb_y = address_coordinates(address, geometry)

    if dependent:
        if preceding_independent is None:
            raise ValueError(
                "dependent slice segment has no preceding independent segment in picture"
            )
        return replace(
            preceding_independent,
            nal_number=nal_number,
            nal_unit_type=nal_type,
            first_slice_segment_in_pic_flag=first,
            no_output_of_prior_pics_flag=no_output,
            pps_id=pps_id,
            dependent_slice_segment_flag=1,
            slice_segment_address=address,
        slice_segment_ctb_x=ctb_x,
        slice_segment_ctb_y=ctb_y,
        pic_width_in_ctbs_y=geometry.pic_width_in_ctbs_y,
        pic_height_in_ctbs_y=geometry.pic_height_in_ctbs_y,
        pic_size_in_ctbs_y=geometry.pic_size_in_ctbs_y,
        slice_segment_address_bit_count=geometry.address_bit_count,
            slice_segment_ctb_x=ctb_x,
            slice_segment_ctb_y=ctb_y,
            pic_width_in_ctbs_y=geometry.pic_width_in_ctbs_y,
            pic_height_in_ctbs_y=geometry.pic_height_in_ctbs_y,
            pic_size_in_ctbs_y=geometry.pic_size_in_ctbs_y,
            slice_segment_address_bit_count=geometry.address_bit_count,
            inherited_from_nal_number=preceding_independent.nal_number,
            header_bits_consumed=reader.position,
            header_bytes_covered=(reader.position + 7) // 8,
            parser_status="dependent_header_complete_fields_inherited",
        )

    for _ in range(pps.num_extra_slice_header_bits):
        reader.bit()
    slice_type = reader.ue()
    pic_output_flag = reader.bit() if pps.output_flag_present_flag else 1
    colour_plane_id = reader.bits(2) if sps.separate_colour_plane_flag else 0
    poc_lsb = None
    if nal_type not in {19, 20}:
        poc_lsb = reader.bits(sps.log2_max_poc_lsb)

    return SliceSegmentHeader(
        nal_number=nal_number,
        nal_unit_type=nal_type,
        first_slice_segment_in_pic_flag=first,
        no_output_of_prior_pics_flag=no_output,
        pps_id=pps_id,
        dependent_slice_segment_flag=0,
        slice_segment_address=address,
        inherited_from_nal_number=None,
        slice_type=slice_type,
        pic_output_flag=pic_output_flag,
        colour_plane_id=colour_plane_id,
        poc_lsb=poc_lsb,
        header_bits_consumed=reader.position,
        header_bytes_covered=(reader.position + 7) // 8,
        parser_status="independent_header_core_complete",
    )


def parse_segment_sequence(
    nals: list[dict[str, object]],
    pps_map: dict[int, PPS],
    sps_map: dict[int, SPS],
) -> dict[str, object]:
    segments: list[SliceSegmentHeader] = []
    errors: list[dict[str, object]] = []
    current_picture = 0
    preceding_independent: SliceSegmentHeader | None = None

    for nal in nals:
        nal_type = int(nal["nal_unit_type"])
        if nal_type >= 32:
            continue
        nal_number = int(nal["nal_number"])
        try:
            probe = BitReader(rbsp(bytes(nal["payload"])[2:]))
            first = probe.bit()
            if first:
                current_picture += 1
                preceding_independent = None
            header = parse_slice_segment_header(
                bytes(nal["payload"]),
                nal_type,
                nal_number,
                pps_map,
                sps_map,
                preceding_independent,
            )
            if not header.dependent_slice_segment_flag:
                preceding_independent = header
            row = asdict(header)
            row["picture_number"] = current_picture
            segments.append(header)
        except (KeyError, ValueError) as exc:
            errors.append(
                {
                    "nal_number": nal_number,
                    "nal_unit_type": nal_type,
                    "error": str(exc),
                }
            )

    rows: list[dict[str, Any]] = []
    picture_number = 0
    for header in segments:
        if header.first_slice_segment_in_pic_flag:
            picture_number += 1
        row = asdict(header)
        row["picture_number"] = picture_number
        rows.append(row)

    findings = []
    for error in errors:
        if "dependent slice segment has no preceding independent" in str(error["error"]):
            findings.append(
                {
                    "id": "HEVC_ORPHAN_DEPENDENT_SLICE_SEGMENT",
                    "severity": "high",
                    "description": "A dependent slice segment was encountered without a preceding independent segment in the current picture.",
                    "evidence_refs": [
                        f"hevc_bitstream/slice_segments.json#nal-{error['nal_number']}"
                    ],
                    "requires_reference": False,
                    "host_profile": None,
                    "observations": error,
                }
            )

    return {
        "segments": rows,
        "errors": errors,
        "findings": findings,
        "segment_count": len(rows),
        "dependent_segment_count": sum(
            int(row["dependent_slice_segment_flag"]) for row in rows
        ),
    }

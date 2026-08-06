from __future__ import annotations

from video_forensics.native.hevc_semantic_compare import compare, parse_ffmpeg_trace


def primary() -> dict[str, object]:
    return {
        "nal_units": [
            {
                "nal_number": 1,
                "nal_unit_type": 33,
                "payload": {
                    "sps": {
                        "sps_seq_parameter_set_id": 0,
                        "pic_width_in_luma_samples": 1920,
                    }
                },
            },
            {
                "nal_number": 2,
                "nal_unit_type": 34,
                "payload": {"pps": {"pps_pic_parameter_set_id": 0}},
            },
        ]
    }


def test_semantic_comparison_matches_shared_fields() -> None:
    legacy = {
        "sps": [
            {
                "fields": {
                    "sps_seq_parameter_set_id": 0,
                    "pic_width_in_luma_samples": 1920,
                }
            }
        ],
        "pps": [{"fields": {"pps_pic_parameter_set_id": 0}}],
    }
    result = compare(
        primary(),
        legacy,
        "sps_seq_parameter_set_id 1 = 0\npps_pic_parameter_set_id 1 = 0\n",
    )
    assert result["field_mismatch_count"] == 0
    assert result["legacy_semantic_agreement"] is True
    assert result["authoritative_for_high_weight"] is True


def test_ffmpeg_trace_parser_preserves_repeated_values() -> None:
    parsed = parse_ffmpeg_trace(
        "nal_unit_type 100001 = 33\nnal_unit_type 100010 = 34\n"
    )
    assert parsed["nal_unit_type"] == [33, 34]

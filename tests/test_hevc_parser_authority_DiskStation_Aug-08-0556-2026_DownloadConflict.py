from __future__ import annotations

from video_forensics.native.hevc_parser_authority import compare


def primary() -> dict[str, object]:
    return {
        "nal_count": 2,
        "nal_units": [
            {"nal_unit_type": 33},
            {"nal_unit_type": 34},
        ],
    }


def test_legacy_is_only_comparison_backend() -> None:
    result = compare(
        primary(),
        {"success": True, "returncode": 0},
        {
            "status": "comparison_only",
            "nal_count": 2,
            "nal_unit_types": [33, 34],
        },
    )
    assert result["legacy_agreement"] is True
    assert result["authoritative_for_high_weight"] is True


def test_high_weight_authority_requires_control_backend() -> None:
    result = compare(
        primary(),
        {"success": False, "returncode": 1},
        {"status": "not_requested"},
    )
    assert result["authoritative_for_high_weight"] is False

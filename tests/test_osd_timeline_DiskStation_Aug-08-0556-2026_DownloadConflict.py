from __future__ import annotations

from video_forensics.native.osd_timeline import merge, timeline_findings


def test_merge_maps_pts_by_frame_number() -> None:
    osd = {"readings": [{"frame_number": 2, "ocr_text": "x", "parsed_timestamp": None}]}
    rows = merge(osd, [{"frame_number": 2, "pts_seconds": 1.25}])
    assert rows[0]["pts_seconds"] == 1.25


def test_timeline_flags_missing_and_backward_pts() -> None:
    rows = [
        {"frame_number": 1, "pts_seconds": 1.0},
        {"frame_number": 2, "pts_seconds": None},
        {"frame_number": 3, "pts_seconds": 0.5},
    ]
    findings = timeline_findings(rows)
    assert [item["id"] for item in findings] == [
        "OSD_TIMELINE_PTS_ABSENT_RANGE",
        "OSD_TIMELINE_PTS_NON_MONOTONIC",
    ]

from __future__ import annotations

from video_forensics.tools.gop import _build_gops, _findings, _normalize_frames


def test_builds_gops_from_key_frames() -> None:
    frames = _normalize_frames(
        {
            "frames": [
                {"media_type": "video", "key_frame": 1, "pict_type": "I", "pkt_size": "10"},
                {"media_type": "video", "key_frame": 0, "pict_type": "B", "pkt_size": "4"},
                {"media_type": "video", "key_frame": 0, "pict_type": "P", "pkt_size": "6"},
                {"media_type": "video", "key_frame": 1, "pict_type": "I", "pkt_size": "11"},
                {"media_type": "video", "key_frame": 0, "pict_type": "P", "pkt_size": "7"},
            ]
        }
    )
    gops = _build_gops(frames)
    assert [item["length_frames"] for item in gops] == [3, 2]
    assert gops[0]["picture_types"] == "IBP"
    assert gops[0]["packet_bytes"] == 20


def test_reports_frames_before_first_key_frame() -> None:
    frames = _normalize_frames(
        {
            "frames": [
                {"media_type": "video", "key_frame": 0, "pict_type": "P"},
                {"media_type": "video", "key_frame": 1, "pict_type": "I"},
            ]
        }
    )
    findings = _findings(frames, _build_gops(frames))
    assert findings[0] == {"kind": "frames_before_first_key_frame", "frame_count": 1}


def test_reports_missing_key_frames() -> None:
    frames = _normalize_frames(
        {"frames": [{"media_type": "video", "key_frame": 0, "pict_type": "P"}]}
    )
    assert _findings(frames, []) == [{"kind": "no_key_frames_reported"}]

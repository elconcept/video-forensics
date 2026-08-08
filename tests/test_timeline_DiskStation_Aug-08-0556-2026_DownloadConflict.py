from __future__ import annotations

from video_forensics.tools.timeline import _anomalies, _normalize_frames, _rate


def test_normalizes_frames_and_detects_duplicate_pts() -> None:
    payload = {
        "frames": [
            {"media_type": "video", "pts_time": "0.000", "pkt_duration_time": "0.040"},
            {"media_type": "video", "pts_time": "0.040", "pkt_duration_time": "0.040"},
            {"media_type": "video", "pts_time": "0.040", "pkt_duration_time": "0.080"},
        ]
    }
    frames = _normalize_frames(payload)
    findings = _anomalies(frames)
    assert len(frames) == 3
    assert any(item["kind"] == "duplicate_pts" for item in findings)


def test_detects_non_monotonic_pts_and_missing_pts() -> None:
    frames = _normalize_frames(
        {
            "frames": [
                {"media_type": "video", "pts_time": "1.0"},
                {"media_type": "video", "pts_time": "0.5"},
                {"media_type": "video"},
            ]
        }
    )
    kinds = [item["kind"] for item in _anomalies(frames)]
    assert "non_monotonic_pts" in kinds
    assert "missing_pts_time" in kinds


def test_rate_parsing() -> None:
    assert _rate("30000/1001") is not None
    assert _rate("0/0") is None
    assert _rate("N/A") is None

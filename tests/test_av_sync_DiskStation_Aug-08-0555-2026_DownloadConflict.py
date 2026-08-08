from __future__ import annotations

from video_forensics.tools.av_sync import _audio_bounds, _findings, _video_bounds


def test_calculates_video_and_audio_bounds() -> None:
    video_rows = [
        {"pts_time": "0.0", "pkt_duration_time": "0.04"},
        {"pts_time": "0.04", "pkt_duration_time": "0.04"},
    ]
    audio_rows = [
        {"pts_time": "0.0", "duration_time": "0.02"},
        {"pts_time": "0.06", "duration_time": "0.02"},
    ]
    assert _video_bounds(video_rows) == (0.0, 0.08)
    assert _audio_bounds(audio_rows) == (0.0, 0.08)


def test_reports_start_end_and_relative_drift() -> None:
    findings = _findings(0.0, 10.0, 0.2, 10.5)
    kinds = {finding["kind"] for finding in findings}
    assert "av_start_offset_candidate" in kinds
    assert "av_end_offset_candidate" in kinds
    assert "av_relative_drift_candidate" in kinds


def test_reports_missing_audio_timeline() -> None:
    assert _findings(0.0, 1.0, None, None) == [
        {"kind": "no_audio_timeline_available"}
    ]


def test_accepts_aligned_stream_bounds() -> None:
    assert _findings(0.0, 10.0, 0.01, 10.05) == []

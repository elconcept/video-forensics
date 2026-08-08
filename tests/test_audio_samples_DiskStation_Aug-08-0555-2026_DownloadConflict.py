from __future__ import annotations

from pathlib import Path

from video_forensics.native.audio_samples import analyze, number


def test_number_handles_absent_values() -> None:
    assert number("1.25") == 1.25
    assert number("N/A") is None
    assert number(None) is None


def test_missing_tools_degrade_gracefully(tmp_path: Path) -> None:
    source = tmp_path / "input.mp4"
    source.write_bytes(b"video")
    result = analyze(
        source,
        tmp_path / "output",
        ffmpeg=None,
        ffprobe=None,
        host_profile_id="host-a",
    )
    assert result["status"] == "unavailable"
    assert result["missing_tools"] == ["ffmpeg", "ffprobe"]
    assert (tmp_path / "output" / "audio_samples.json").is_file()

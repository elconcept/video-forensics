from __future__ import annotations

from pathlib import Path

from video_forensics.native.decoder_frame_timestamps import build_command, parse_showinfo


def test_parse_showinfo_preserves_decoder_order() -> None:
    text = (
        "[Parsed_showinfo_0] n:   0 pts:      0 pts_time:0\n"
        "[Parsed_showinfo_0] n:   1 pts:   1001 pts_time:0.0667333\n"
    )
    rows = parse_showinfo(text)
    assert rows == [
        {"frame_number": 1, "decoder_frame_index": 0, "pts": 0, "pts_time": 0.0},
        {
            "frame_number": 2,
            "decoder_frame_index": 1,
            "pts": 1001,
            "pts_time": 0.0667333,
        },
    ]


def test_hardware_command_downloads_before_showinfo() -> None:
    command = build_command(
        Path("ffmpeg"),
        Path("input.mp4"),
        ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
    )
    filter_value = command[command.index("-vf") + 1]
    assert filter_value == "hwdownload,format=nv12,showinfo"
    assert command[-3:] == ["null", "-"] or command[-3:] == ["-f", "null", "-"]

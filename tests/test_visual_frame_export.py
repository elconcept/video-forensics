from __future__ import annotations

from pathlib import Path

from video_forensics.native.visual_frame_export import (
    export_command,
    hardware_download_filter,
)


def test_lossless_command_uses_png_image2_and_ignore_err() -> None:
    command = export_command(
        Path("/usr/bin/ffmpeg"),
        Path("input.mp4"),
        ["-threads", "1"],
        Path("frame_%09d.png"),
        email=False,
    )
    assert ["-err_detect", "ignore_err"] == command[5:7]
    assert "png" in command
    assert command[-2:] == ["image2", "frame_%09d.png"]


def test_email_command_scales_and_uses_mjpeg() -> None:
    command = export_command(
        Path("ffmpeg"),
        Path("input.mp4"),
        [],
        Path("frame_%09d.jpg"),
        email=True,
    )
    assert "scale=1280:-2:flags=lanczos" in command
    assert "mjpeg" in command
    assert "3" in command


def test_hardware_profiles_require_download_filter() -> None:
    assert hardware_download_filter(["-hwaccel", "cuda"]) == "hwdownload,format=nv12"
    assert hardware_download_filter(["-threads", "1"]) is None

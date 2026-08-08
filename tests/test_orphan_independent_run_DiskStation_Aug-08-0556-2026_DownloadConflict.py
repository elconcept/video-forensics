from __future__ import annotations

from pathlib import Path

import pytest

from video_forensics.native.orphan_independent_run import run


def test_requires_dec265_before_creating_result_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stream = tmp_path / "source.h265"
    stream.write_bytes(b"stream")
    plan = tmp_path / "plan.json"
    plan.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "video_forensics.native.orphan_independent_run.find_dec265",
        lambda _: None,
    )
    with pytest.raises(FileNotFoundError, match="dec265"):
        run(
            stream,
            plan,
            tmp_path / "output",
            dec265_path=None,
            ffmpeg_path=None,
            pixel_format="yuv420p",
            threads=0,
            sigma_threshold=8.0,
            host_profile=None,
            timeout=60,
        )
    assert not (tmp_path / "output").exists()

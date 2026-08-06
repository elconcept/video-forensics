from __future__ import annotations

import json
from pathlib import Path

from video_forensics.tools.metadata import ToolSpec, analyze


def _tool(tmp_path: Path, name: str, payload: object) -> ToolSpec:
    executable = tmp_path / name
    encoded = json.dumps(payload)
    executable.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  -version|--Version|-ver) echo 'mock 1.0'; exit 0 ;;\n"
        "esac\n"
        f"printf '%s\\n' '{encoded}'\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    version_args = {
        "ffprobe": ("-version",),
        "mediainfo": ("--Version",),
        "exiftool": ("-ver",),
    }[name]
    return ToolSpec(name, executable, version_args)


def test_metadata_preserves_raw_outputs_and_summary(tmp_path: Path) -> None:
    video = tmp_path / "sample.mov"
    output = tmp_path / "results"
    video.write_bytes(b"video")
    tools = (
        _tool(tmp_path, "ffprobe", {"streams": [{"index": 0}], "format": {"size": "5"}}),
        _tool(tmp_path, "mediainfo", {"media": {"track": [{"@type": "General"}]}}),
        _tool(tmp_path, "exiftool", [{"SourceFile": "sample.mov"}]),
    )

    result = analyze(video, output, tools=tools)

    assert result["summary"]["ffprobe_stream_count"] == 1
    assert result["summary"]["mediainfo_track_count"] == 1
    assert result["summary"]["exiftool_record_count"] == 1
    for name in ("ffprobe", "mediainfo", "exiftool"):
        assert (output / "metadata" / "raw" / f"{name}.json").is_file()
    saved = json.loads((output / "metadata" / "metadata.json").read_text())
    assert saved["tools"]["ffprobe"]["version_output"] == "mock 1.0"

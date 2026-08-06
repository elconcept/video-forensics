from __future__ import annotations

import hashlib
import json
from pathlib import Path

from video_forensics.tools.integrity import analyze


def test_integrity_writes_expected_hashes(tmp_path: Path) -> None:
    content = b"forensic-test\x00\x01\n"
    video = tmp_path / "sample.bin"
    output = tmp_path / "result"
    video.write_bytes(content)

    result = analyze(video, output)

    assert result["hashes"]["sha256"] == hashlib.sha256(content).hexdigest()
    assert result["hashes"]["sha512"] == hashlib.sha512(content).hexdigest()
    assert result["bytes_read"] == len(content)
    saved = json.loads((output / "integrity" / "hashes.json").read_text())
    assert saved["input_unchanged_during_read"] is True

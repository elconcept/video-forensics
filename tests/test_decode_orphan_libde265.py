from __future__ import annotations

import json
from pathlib import Path

import pytest

from video_forensics.native.decode_orphan_libde265 import decode_variants


def test_rejects_variant_hash_mismatch(tmp_path: Path) -> None:
    streams = tmp_path / "streams"
    streams.mkdir()
    (streams / "variant.h265").write_bytes(b"stream")
    (streams / "orphan_streams.json").write_text(
        json.dumps(
            {
                "variants": [
                    {
                        "file": "variant.h265",
                        "sha256": "wrong",
                        "reference_nal_number": 4,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        decode_variants(
            streams,
            tmp_path / "output",
            width=64,
            height=64,
            pixel_format="yuv420p",
            threads=0,
            dec265=None,
            ffmpeg=Path("/bin/true"),
            host_profile_id=None,
            timeout=60,
        )

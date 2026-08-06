from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from time import monotonic
from typing import BinaryIO

from video_forensics.manifest import InputIdentity, atomic_write_json, utc_now

CHUNK_SIZE = 8 * 1024 * 1024


def _hash_stream(handle: BinaryIO) -> tuple[str, str, int]:
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    total = 0
    while chunk := handle.read(CHUNK_SIZE):
        sha256.update(chunk)
        sha512.update(chunk)
        total += len(chunk)
    return sha256.hexdigest(), sha512.hexdigest(), total


def analyze(video: Path, output_dir: Path) -> dict[str, object]:
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError(f"input is not a regular file: {video}")

    before = InputIdentity.capture(video)
    started = monotonic()
    with video.open("rb", buffering=0) as handle:
        sha256, sha512, bytes_read = _hash_stream(handle)
    after = InputIdentity.capture(video)

    if before != after:
        raise RuntimeError("input identity changed while hashes were being calculated")
    if bytes_read != before.size_bytes:
        raise RuntimeError(
            f"read-size mismatch: expected {before.size_bytes}, read {bytes_read}"
        )

    result: dict[str, object] = {
        "schema_version": 1,
        "stage": "integrity",
        "completed_at_utc": utc_now(),
        "duration_seconds": round(monotonic() - started, 6),
        "input_before": asdict(before),
        "input_after": asdict(after),
        "bytes_read": bytes_read,
        "hashes": {"sha256": sha256, "sha512": sha512},
        "input_unchanged_during_read": True,
    }
    atomic_write_json(output_dir / "integrity" / "hashes.json", result)
    return result

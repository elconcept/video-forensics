from __future__ import annotations

import hashlib

import numpy as np

from video_forensics.tools.duplicates import (
    _difference_hash,
    _exact_groups,
    _hamming,
    _near_adjacent,
    _repeated_sequences,
)


def row(frame_number: int, content: bytes, difference_hash: int = 0) -> dict[str, object]:
    return {
        "frame_number": frame_number,
        "sha256": hashlib.sha256(content).hexdigest(),
        "difference_hash": format(difference_hash, "0288x"),
    }


def test_difference_hash_and_hamming() -> None:
    frame = np.tile(np.arange(64, dtype=np.uint8), (36, 1))
    first = _difference_hash(frame)
    second = _difference_hash(frame.copy())
    assert first == second
    assert _hamming(first, second) == 0


def test_exact_duplicate_groups() -> None:
    rows = [row(1, b"a"), row(2, b"b"), row(3, b"a")]
    groups = _exact_groups(rows)
    assert len(groups) == 1
    assert groups[0]["frames"] == [1, 3]


def test_near_adjacent_pairs() -> None:
    rows = [row(1, b"a", 0), row(2, b"b", 1), row(3, b"c", 255)]
    findings = _near_adjacent(rows)
    assert len(findings) == 1
    assert findings[0]["first_frame"] == 1
    assert findings[0]["second_frame"] == 2


def test_repeated_exact_sequence() -> None:
    rows = [
        row(1, b"a"),
        row(2, b"b"),
        row(3, b"c"),
        row(4, b"a"),
        row(5, b"b"),
        row(6, b"x"),
    ]
    sequences = _repeated_sequences(rows)
    assert sequences[0]["first_start_frame"] == 1
    assert sequences[0]["second_start_frame"] == 4
    assert sequences[0]["length_frames"] == 2

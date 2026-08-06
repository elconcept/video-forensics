from __future__ import annotations

import numpy as np

from video_forensics.native.compare_perceptual_runs import metrics


def test_identical_frames() -> None:
    frame = np.arange(100, dtype=np.float64)
    result = metrics(frame, frame.copy())
    assert result["mae"] == 0.0
    assert result["rmse"] == 0.0
    assert result["ncc"] == 1.0
    assert result["identical_pixel_fraction"] == 1.0


def test_shifted_frames_preserve_perfect_correlation() -> None:
    left = np.arange(100, dtype=np.float64)
    right = left + 10.0
    result = metrics(left, right)
    assert result["mae"] == 10.0
    assert result["ncc"] == 1.0
    assert result["identical_pixel_fraction"] == 0.0

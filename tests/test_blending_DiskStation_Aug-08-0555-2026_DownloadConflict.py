from __future__ import annotations

import numpy as np

from video_forensics.tools.blending import _findings, _fit_blend


def test_fit_blend_recovers_linear_intermediate_frame() -> None:
    previous = np.zeros((8, 8), dtype=np.uint8)
    following = np.full((8, 8), 200, dtype=np.uint8)
    current = np.full((8, 8), 100, dtype=np.uint8)
    result = _fit_blend(previous, current, following)
    assert result["alpha"] == 0.5
    assert result["residual"] == 0.0
    assert result["residual_ratio"] == 0.0


def test_findings_accepts_supported_candidate() -> None:
    rows = [
        {
            "frame_number": 10,
            "alpha": 0.5,
            "residual": 1.0,
            "baseline": 10.0,
            "residual_ratio": 0.1,
            "mae_previous": 12.0,
            "mae_following": 11.0,
        }
    ]
    findings = _findings(rows)
    assert findings[0]["frame_number"] == 10


def test_findings_rejects_static_neighbors() -> None:
    rows = [
        {
            "frame_number": 10,
            "alpha": 0.5,
            "residual": 0.0,
            "baseline": 0.1,
            "residual_ratio": 0.0,
            "mae_previous": 0.1,
            "mae_following": 0.1,
        }
    ]
    assert _findings(rows) == []

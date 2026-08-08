from __future__ import annotations

import numpy as np

from video_forensics.native.osd_glyph_metrics import components, summarize


def test_components_measure_baseline_and_geometry() -> None:
    mask = np.zeros((8, 10), dtype=bool)
    mask[2:7, 1:3] = True
    mask[3:7, 6:9] = True
    found = components(mask, minimum_pixels=3)
    assert found[0] == {
        "pixel_count": 10,
        "x": 1,
        "y": 2,
        "width": 2,
        "height": 5,
        "baseline": 6,
    }
    assert found[1]["baseline"] == 6


def test_summary_reports_ranges() -> None:
    result = summarize(
        [
            [
                {"baseline": 5, "height": 4, "width": 2},
                {"baseline": 7, "height": 6, "width": 3},
            ]
        ]
    )
    assert result["component_count"] == 2
    assert result["baseline_range"] == 2
    assert result["height_range"] == 2

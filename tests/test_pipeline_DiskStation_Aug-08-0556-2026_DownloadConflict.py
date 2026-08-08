from __future__ import annotations

import pytest

from video_forensics.pipeline import (
    DEFAULT_STAGES,
    OPTIONAL_STAGES,
    parse_stages,
    resolve_stages,
    supported_stages,
    validate_stage_options,
)


def test_default_pipeline_excludes_optional_large_or_reference_stages() -> None:
    assert "extract_frames" not in DEFAULT_STAGES
    assert "reference_compare" not in DEFAULT_STAGES
    assert set(OPTIONAL_STAGES) == {"extract_frames", "reference_compare"}


def test_resolves_transitive_dependencies_in_execution_order() -> None:
    assert resolve_stages(["continuity"]) == [
        "timeline",
        "gop",
        "frame_metrics",
        "continuity",
    ]
    assert resolve_stages(["av_sync"]) == ["timeline", "audio", "av_sync"]


def test_resolve_deduplicates_shared_dependencies() -> None:
    resolved = resolve_stages(["continuity", "compression"])
    assert resolved.count("gop") == 1
    assert resolved.index("gop") < resolved.index("continuity")
    assert resolved.index("gop") < resolved.index("compression")


def test_parse_rejects_unknown_and_duplicate_stages() -> None:
    with pytest.raises(ValueError, match="unsupported stages"):
        parse_stages("unknown")
    with pytest.raises(ValueError, match="cannot be repeated"):
        parse_stages("gop,gop")


def test_reference_comparison_requires_reference_output() -> None:
    stages = resolve_stages(["reference_compare"])
    with pytest.raises(ValueError, match="--reference-output"):
        validate_stage_options(stages, None)
    validate_stage_options(stages, object())


def test_supported_stages_contains_all_defaults_and_optionals() -> None:
    supported = set(supported_stages())
    assert set(DEFAULT_STAGES) <= supported
    assert set(OPTIONAL_STAGES) <= supported

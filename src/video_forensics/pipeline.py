from __future__ import annotations

STAGE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "integrity": (),
    "metadata": (),
    "container_structure": (),
    "timeline": (),
    "gop": (),
    "frame_metrics": (),
    "continuity": ("timeline", "gop", "frame_metrics"),
    "duplicates": (),
    "blending": (),
    "compression": ("gop",),
    "audio": (),
    "av_sync": ("timeline", "audio"),
    "extract_frames": (),
    "reference_compare": ("metadata", "container_structure", "gop"),
    "report": (),
}

DEFAULT_STAGES = (
    "integrity",
    "metadata",
    "container_structure",
    "timeline",
    "gop",
    "frame_metrics",
    "continuity",
    "duplicates",
    "blending",
    "compression",
    "audio",
    "av_sync",
    "report",
)

OPTIONAL_STAGES = ("extract_frames", "reference_compare")


def supported_stages() -> tuple[str, ...]:
    return tuple(STAGE_DEPENDENCIES)


def parse_stages(raw: str) -> list[str]:
    stages = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(stages) - set(STAGE_DEPENDENCIES))
    if unknown:
        raise ValueError(f"unsupported stages: {', '.join(unknown)}")
    if not stages:
        raise ValueError("at least one stage is required")
    if len(stages) != len(set(stages)):
        raise ValueError("stages cannot be repeated")
    return stages


def resolve_stages(requested: list[str]) -> list[str]:
    resolved: list[str] = []
    visiting: set[str] = set()

    def add(stage: str) -> None:
        if stage in resolved:
            return
        if stage in visiting:
            raise RuntimeError(f"cyclic stage dependency involving: {stage}")
        visiting.add(stage)
        for dependency in STAGE_DEPENDENCIES[stage]:
            add(dependency)
        visiting.remove(stage)
        resolved.append(stage)

    for stage in requested:
        add(stage)
    return resolved


def validate_stage_options(stages: list[str], reference_output: object | None) -> None:
    if "reference_compare" in stages and reference_output is None:
        raise ValueError("--reference-output is required when reference_compare is selected")

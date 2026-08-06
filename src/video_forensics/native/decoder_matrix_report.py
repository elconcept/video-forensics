from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"required JSON file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return payload


def frame_count_finding(matrix: dict[str, Any]) -> dict[str, object] | None:
    counts = {
        str(run_id): int(count)
        for run_id, count in matrix.get("frame_counts", {}).items()
    }
    if len(set(counts.values())) <= 1:
        return None
    groups: dict[int, list[str]] = defaultdict(list)
    for run_id, count in counts.items():
        groups[count].append(run_id)
    return {
        "id": "DECODER_FRAME_COUNT_DIVERGENCE",
        "severity": "high",
        "description": "Decoder paths returned different numbers of video frames for the same verified input.",
        "evidence_refs": ["decoder_comparison/decoder_matrix.json"],
        "requires_reference": False,
        "host_profile": None,
        "observations": {
            "frame_counts": counts,
            "groups": [
                {"frame_count": count, "decoder_runs": sorted(run_ids)}
                for count, run_ids in sorted(groups.items())
            ],
            "minimum_frame_count": min(counts.values()),
            "maximum_frame_count": max(counts.values()),
            "frame_count_range": max(counts.values()) - min(counts.values()),
        },
        "interpretation_boundary": (
            "The result establishes non-uniform decoder handling. It does not by itself identify "
            "which output is the intended visual representation of the coded stream."
        ),
    }


def first_divergence_finding(matrix: dict[str, Any]) -> dict[str, object] | None:
    frame = matrix.get("first_divergent_frame")
    if frame is None:
        return None
    return {
        "id": "DECODER_CONTENT_DIVERGENCE",
        "severity": "high",
        "description": "Decoder outputs first diverged in frame presence or exact frame checksum at the recorded output position.",
        "evidence_refs": [
            "decoder_comparison/decoder_matrix.json",
            "decoder_comparison/frame_comparison.csv",
        ],
        "requires_reference": False,
        "host_profile": None,
        "observations": {"first_divergent_frame": int(frame)},
        "interpretation_boundary": (
            "Exact checksum divergence can include pixel-format and conversion differences. "
            "Use normalized and perceptual comparisons to determine its visual magnitude."
        ),
    }


def missing_reference_finding(matrix: dict[str, Any]) -> dict[str, object] | None:
    values = {
        str(run_id): [int(value) for value in pocs]
        for run_id, pocs in matrix.get("missing_reference_pocs", {}).items()
        if pocs
    }
    if not values:
        return None
    return {
        "id": "DECODER_MISSING_REFERENCE_DIAGNOSTICS",
        "severity": "high",
        "description": "One or more decoder runs emitted missing-reference POC diagnostics.",
        "evidence_refs": ["decoder_comparison/decoder_matrix.json"],
        "requires_reference": False,
        "host_profile": None,
        "observations": {
            "decoder_runs": values,
            "diagnostic_count": sum(len(pocs) for pocs in values.values()),
        },
        "interpretation_boundary": (
            "Decoder diagnostics describe the decoding process. They must be correlated with "
            "bitstream-level NAL, POC, and reference-picture analysis."
        ),
    }


def perceptual_pair_findings(perceptual: dict[str, Any] | None) -> list[dict[str, object]]:
    if perceptual is None:
        return []
    findings: list[dict[str, object]] = []
    for pair in perceptual.get("pairs", []):
        compared = [
            frame
            for frame in pair.get("frames", [])
            if frame.get("status") == "compared"
        ]
        divergent = [
            frame
            for frame in compared
            if frame.get("mae") is not None and float(frame["mae"]) > 0.0
        ]
        missing = [
            frame
            for frame in pair.get("frames", [])
            if frame.get("status") == "missing_in_one_run"
        ]
        if not divergent and not missing:
            continue
        first = min(
            [int(frame["frame_number"]) for frame in divergent + missing],
            default=None,
        )
        findings.append(
            {
                "id": "DECODER_PAIR_VISUAL_DIVERGENCE",
                "severity": "medium",
                "description": "A decoder pair produced different normalized visual output or a missing frame.",
                "evidence_refs": ["perceptual_comparison/perceptual_comparison.json"],
                "requires_reference": False,
                "host_profile": None,
                "observations": {
                    "left_decoder": pair.get("left"),
                    "right_decoder": pair.get("right"),
                    "first_divergent_frame": first,
                    "different_frame_count": len(divergent),
                    "missing_frame_count": len(missing),
                    "minimum_ncc": min(
                        (
                            float(frame["ncc"])
                            for frame in divergent
                            if frame.get("ncc") is not None
                        ),
                        default=None,
                    ),
                    "maximum_mae": max(
                        (float(frame["mae"]) for frame in divergent),
                        default=None,
                    ),
                },
                "interpretation_boundary": (
                    "A pairwise difference may be decoder-specific, driver-specific, or caused "
                    "by conversion behavior. Bitstream origin requires broader cross-path correlation."
                ),
            }
        )
    return findings


def build_report(
    matrix_path: Path,
    output: Path,
    perceptual_path: Path | None = None,
) -> dict[str, object]:
    matrix = read_json(matrix_path.expanduser().resolve(strict=True))
    perceptual = (
        None
        if perceptual_path is None
        else read_json(perceptual_path.expanduser().resolve(strict=True))
    )
    if perceptual is not None:
        matrix_hash = matrix.get("input_sha256")
        perceptual_hash = perceptual.get("input_sha256")
        if matrix_hash is None or perceptual_hash is None or matrix_hash != perceptual_hash:
            raise ValueError("matrix and perceptual comparison do not share one verified input SHA-256")

    findings: list[dict[str, object]] = []
    for finding in (
        frame_count_finding(matrix),
        missing_reference_finding(matrix),
        first_divergence_finding(matrix),
    ):
        if finding is not None:
            findings.append(finding)
    findings.extend(perceptual_pair_findings(perceptual))

    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda item: severity_order.get(str(item["severity"]), 99))
    result: dict[str, object] = {
        "schema_version": 1,
        "module": "decoder_matrix_report",
        "input_sha256": matrix.get("input_sha256"),
        "finding_count": len(findings),
        "findings": findings,
        "interpretation_policy": {
            "frame_count_divergence": "high",
            "missing_reference_diagnostics": "high",
            "exact_content_divergence": "high",
            "pairwise_visual_divergence": "medium",
            "rule": (
                "Decoder divergence is reported as a diagnostic property requiring bitstream "
                "analysis. Agreement is not treated as an authenticity verdict."
            ),
        },
    }
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "decoder_matrix_findings.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-decoder-matrix-report")
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--perceptual", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build_report(args.matrix, args.output, args.perceptual)
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"finding_count": result["finding_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

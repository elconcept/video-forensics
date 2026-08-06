from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from video_forensics.native.decode_orphan_variants import decode_all
from video_forensics.native.orphan_recovery import run_recovery
from video_forensics.native.orphan_recovery_report import build_report
from video_forensics.native.orphan_stream_builder import build
from video_forensics.native.verify_orphan_decoders import verify


def find_ffmpeg(explicit: str | None) -> Path:
    candidate = explicit or shutil.which("ffmpeg")
    if not candidate:
        raise FileNotFoundError("cannot find ffmpeg; pass --ffmpeg")
    return Path(candidate).expanduser().resolve(strict=True)


def run_pipeline(
    annex_b: Path,
    plan: Path,
    output: Path,
    *,
    ffmpeg: Path,
    sigma_threshold: float,
    external_decoder_roots: list[Path],
    host_profile: Path | None,
    timeout: int,
) -> dict[str, object]:
    annex_b = annex_b.expanduser().resolve(strict=True)
    plan = plan.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)

    streams_root = output / "streams"
    libavcodec_root = output / "decoder_libavcodec"
    recovery_root = output / "recovery"
    verification_root = output / "verification"
    report_root = output / "report"

    streams = build(annex_b, plan, streams_root)
    decoded = decode_all(
        streams_root,
        libavcodec_root,
        ffmpeg,
        decoder_id="libavcodec",
        decoder_args=["-threads", "1"],
        timeout=timeout,
    )
    if not decoded["all_successful"]:
        raise RuntimeError("one or more controlled libavcodec decodes failed")
    if not decoded["all_logs_free_of_missing_reference"]:
        raise RuntimeError("controlled libavcodec decode still reports missing references")

    recovery = run_recovery(
        libavcodec_root,
        recovery_root,
        sigma_threshold=sigma_threshold,
    )

    decoder_roots = [libavcodec_root]
    decoder_roots.extend(
        root.expanduser().resolve(strict=True) for root in external_decoder_roots
    )
    verification: dict[str, object] | None = None
    report: dict[str, object] | None = None
    if len(decoder_roots) >= 2:
        verification = verify(decoder_roots, verification_root)
        report = build_report(
            recovery_root,
            verification_root,
            report_root,
            host_profile,
        )

    manifest: dict[str, object] = {
        "schema_version": 1,
        "module": "orphan_pipeline",
        "input": {
            "annex_b": str(annex_b),
            "plan": str(plan),
        },
        "parameters": {
            "sigma_threshold": sigma_threshold,
            "timeout_seconds": timeout,
        },
        "stages": {
            "stream_builder": {
                "status": "completed",
                "variant_count": len(streams["variants"]),
                "output": str(streams_root),
            },
            "libavcodec_decode": {
                "status": "completed",
                "variant_count": decoded["variant_count"],
                "output": str(libavcodec_root),
            },
            "recovery": {
                "status": "completed",
                "frame_count": recovery["frame_count"],
                "output": str(recovery_root),
            },
            "independent_verification": {
                "status": "completed" if verification is not None else "pending",
                "decoder_count": 0 if verification is None else verification["decoder_count"],
                "output": None if verification is None else str(verification_root),
            },
            "report": {
                "status": "completed" if report is not None else "pending",
                "output": None if report is None else str(report_root),
            },
        },
        "interpretation_boundary": (
            "A completed recovery stage without independent verification is provisional. "
            "The structured finding is emitted only when at least one external decoder output is supplied."
        ),
    }
    (output / "orphan_pipeline.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-orphan-pipeline")
    parser.add_argument("annex_b", type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg")
    parser.add_argument("--sigma-threshold", type=float, default=8.0)
    parser.add_argument("--external-decoder-root", action="append", type=Path, default=[])
    parser.add_argument("--host-profile", type=Path)
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = run_pipeline(
            args.annex_b,
            args.plan,
            args.output,
            ffmpeg=find_ffmpeg(args.ffmpeg),
            sigma_threshold=args.sigma_threshold,
            external_decoder_roots=args.external_decoder_root,
            host_profile=args.host_profile,
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        KeyError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result["stages"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

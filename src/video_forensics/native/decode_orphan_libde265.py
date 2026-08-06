from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from video_forensics.native.libde265_run import find_dec265, run_decode
from video_forensics.native.yuv_png_sequence import convert_sequence


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object: {path}")
    return payload


def find_ffmpeg(explicit: str | None) -> Path:
    candidate = explicit or shutil.which("ffmpeg")
    if not candidate:
        raise FileNotFoundError("cannot find ffmpeg; pass --ffmpeg")
    return Path(candidate).expanduser().resolve(strict=True)



def decode_variants(
    streams_root: Path,
    output: Path,
    *,
    width: int,
    height: int,
    pixel_format: str,
    threads: int,
    dec265: Path | None,
    ffmpeg: Path,
    host_profile_id: str | None,
    timeout: int,
) -> dict[str, object]:
    streams_root = streams_root.expanduser().resolve(strict=True)
    manifest = read_json(streams_root / "orphan_streams.json")
    variants = manifest.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("orphan stream manifest contains no variants")
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)

    results: list[dict[str, object]] = []
    for variant in variants:
        source = streams_root / str(variant["file"])
        source = source.resolve(strict=True)
        expected = str(variant["sha256"]).lower()
        actual = sha256(source)
        if actual != expected:
            raise ValueError(f"controlled variant SHA-256 mismatch: {source}")
        reference_nal = int(variant["reference_nal_number"])
        variant_id = f"orphan_ref_nal_{reference_nal:06d}"
        variant_root = output / variant_id
        run_root = variant_root / "decoder_run"
        result = run_decode(
            source,
            run_root,
            binary=dec265,
            width=width,
            height=height,
            pixel_format=pixel_format,
            threads=threads,
            host_profile_id=host_profile_id,
            timeout=timeout,
        )
        record: dict[str, object] = {
            "variant_id": variant_id,
            "reference_nal_number": reference_nal,
            "source": str(source),
            "source_sha256": actual,
            "decoder_status": result["status"],
            "decoder_manifest": str(run_root / "libde265_run.json"),
            "frame_count": result.get("frame_count", 0),
        }
        if result["status"] == "completed":
            yuv = run_root / "decoded.yuv"
            sequence = convert_sequence(
                yuv,
                variant_root / "frames",
                width=width,
                height=height,
                pixel_format=pixel_format,
                ffmpeg=ffmpeg,
                timeout=timeout,
            )
            pngs = sorted((variant_root / "frames").glob("frame_*.png"))
            if len(pngs) != int(result["frame_count"]):
                raise RuntimeError(
                    "libde265 raw-frame count differs from generated PNG count"
                )
            record.update(
                {
                    "status": "completed",
                    "png_frame_count": len(pngs),
                    "frames": [
                        {
                            "frame_number": index,
                            "file": str(path.relative_to(variant_root)),
                            "size_bytes": path.stat().st_size,
                            "sha256": sha256(path),
                        }
                        for index, path in enumerate(pngs, start=1)
                    ],
                    "sequence_manifest": str(variant_root / "frames" / "yuv_png_sequence.json"),
                    "order_policy": sequence["order_policy"],
                }
            )
        else:
            record["status"] = result["status"]
        (variant_root / "manifest.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        results.append(record)

    completed = sum(item["status"] == "completed" for item in results)
    aggregate: dict[str, object] = {
        "schema_version": 1,
        "module": "decode_orphan_libde265",
        "decoder_id": "libde265",
        "host_profile": host_profile_id,
        "parameters": {
            "width": width,
            "height": height,
            "pixel_format": pixel_format,
            "threads": threads,
        },
        "variant_count": len(results),
        "completed_variant_count": completed,
        "all_successful": completed == len(results),
        "variants": results,
    }
    (output / "decoder_manifest.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-decode-orphan-libde265")
    parser.add_argument("streams_root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument(
        "--pixel-format", choices=("yuv420p", "yuv444p", "gray"), default="yuv420p"
    )
    parser.add_argument("--threads", type=int, default=0)
    parser.add_argument("--dec265")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--host-profile-id")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    try:
        result = decode_variants(
            args.streams_root,
            args.output,
            width=args.width,
            height=args.height,
            pixel_format=args.pixel_format,
            threads=args.threads,
            dec265=find_dec265(args.dec265),
            ffmpeg=find_ffmpeg(args.ffmpeg),
            host_profile_id=args.host_profile_id,
            timeout=args.timeout,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        KeyError,
        RuntimeError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"all_successful": result["all_successful"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

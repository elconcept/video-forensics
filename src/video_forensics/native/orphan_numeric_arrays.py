from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def variant_directories(root: Path) -> list[Path]:
    variants = sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and path.name.startswith("orphan_ref_nal_")
    )
    if len(variants) < 2:
        raise ValueError("at least two controlled variant directories are required")
    return variants


def frame_files(variant: Path) -> list[Path]:
    direct = sorted(variant.glob("frame_*.png"))
    if direct:
        return direct
    nested = sorted((variant / "frames").glob("frame_*.png"))
    if nested:
        return nested
    raise ValueError(f"no PNG frames found for variant: {variant}")


def aligned_frames(root: Path) -> tuple[list[Path], list[list[Path]]]:
    variants = variant_directories(root)
    sequences = [frame_files(path) for path in variants]
    counts = {len(sequence) for sequence in sequences}
    if len(counts) != 1:
        raise ValueError(f"controlled variants have different frame counts: {sorted(counts)}")
    names = [[path.name for path in sequence] for sequence in sequences]
    if any(sequence_names != names[0] for sequence_names in names[1:]):
        raise ValueError("controlled variant frame filenames are not aligned")
    return variants, sequences


def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def compute_frame(
    paths: list[Path], sigma_threshold: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    stack = np.stack([load_rgb(path) for path in paths], axis=0)
    if any(frame.shape != stack.shape[1:] for frame in stack):
        raise ValueError("variant frame dimensions differ")
    median = np.median(stack, axis=0).astype(np.float32)
    standard_deviation = np.std(stack.astype(np.float32), axis=0, ddof=0).astype(
        np.float32
    )
    channel_determination_mask = (
        standard_deviation <= sigma_threshold
    ).astype(np.uint8)
    determination_mask = np.all(
        channel_determination_mask == 1, axis=2
    ).astype(np.uint8)
    return (
        median,
        standard_deviation,
        channel_determination_mask,
        determination_mask,
    )


def export_numeric_arrays(
    variants_root: Path,
    output: Path,
    *,
    sigma_threshold: float,
) -> dict[str, object]:
    if sigma_threshold < 0:
        raise ValueError("sigma threshold must be non-negative")
    variants_root = variants_root.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    variants, sequences = aligned_frames(variants_root)
    rows: list[dict[str, object]] = []

    for frame_index in range(len(sequences[0])):
        source_paths = [sequence[frame_index] for sequence in sequences]
        (
            median,
            standard_deviation,
            channel_determination_mask,
            determination_mask,
        ) = compute_frame(source_paths, sigma_threshold)
        frame_number = frame_index + 1
        stem = f"frame_{frame_number:09d}"
        median_path = output / f"{stem}_median.npy"
        std_path = output / f"{stem}_stddev.npy"
        channel_mask_path = output / f"{stem}_channel_determination_mask.npy"
        mask_path = output / f"{stem}_determination_mask.npy"
        archive_path = output / f"{stem}.npz"
        np.save(median_path, median, allow_pickle=False)
        np.save(std_path, standard_deviation, allow_pickle=False)
        np.save(
            channel_mask_path,
            channel_determination_mask,
            allow_pickle=False,
        )
        np.save(mask_path, determination_mask, allow_pickle=False)
        np.savez_compressed(
            archive_path,
            median=median,
            standard_deviation=standard_deviation,
            channel_determination_mask=channel_determination_mask,
            determination_mask=determination_mask,
        )
        rows.append(
            {
                "frame_number": frame_number,
                "source_filename": source_paths[0].name,
                "variant_count": len(source_paths),
                "height": median.shape[0],
                "width": median.shape[1],
                "channels": median.shape[2],
                "median_dtype": str(median.dtype),
                "standard_deviation_dtype": str(standard_deviation.dtype),
                "channel_determination_mask_dtype": str(
                    channel_determination_mask.dtype
                ),
                "determination_mask_dtype": str(determination_mask.dtype),
                "determined_red_count": int(
                    channel_determination_mask[:, :, 0].sum()
                ),
                "determined_green_count": int(
                    channel_determination_mask[:, :, 1].sum()
                ),
                "determined_blue_count": int(
                    channel_determination_mask[:, :, 2].sum()
                ),
                "determined_red_fraction": float(
                    channel_determination_mask[:, :, 0].mean()
                ),
                "determined_green_fraction": float(
                    channel_determination_mask[:, :, 1].mean()
                ),
                "determined_blue_fraction": float(
                    channel_determination_mask[:, :, 2].mean()
                ),
                "determined_pixel_count": int(determination_mask.sum()),
                "pixel_count": int(determination_mask.size),
                "determined_pixel_fraction": float(determination_mask.mean()),
                "median_file": median_path.name,
                "median_sha256": sha256(median_path),
                "standard_deviation_file": std_path.name,
                "standard_deviation_sha256": sha256(std_path),
                "channel_determination_mask_file": channel_mask_path.name,
                "channel_determination_mask_sha256": sha256(
                    channel_mask_path
                ),
                "determination_mask_file": mask_path.name,
                "determination_mask_sha256": sha256(mask_path),
                "archive_file": archive_path.name,
                "archive_sha256": sha256(archive_path),
            }
        )

    with (output / "index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest: dict[str, object] = {
        "schema_version": 1,
        "module": "orphan_numeric_arrays",
        "variants_root": str(variants_root),
        "variant_ids": [path.name for path in variants],
        "variant_count": len(variants),
        "frame_count": len(rows),
        "sigma_threshold": sigma_threshold,
        "array_semantics": {
            "median": "per-channel median across controlled variants, float32",
            "standard_deviation": "population standard deviation per channel across controlled variants, float32",
            "channel_determination_mask": "one independently for each RGB channel whose standard deviation is at or below the threshold, uint8 HxWx3",
            "determination_mask": "one only when all RGB channels of the pixel are determined, uint8 HxW",
        },
        "frames": rows,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="video-forensics-orphan-numeric-arrays")
    parser.add_argument("variants_root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sigma-threshold", type=float, default=8.0)
    args = parser.parse_args()
    try:
        result = export_numeric_arrays(
            args.variants_root,
            args.output,
            sigma_threshold=args.sigma_threshold,
        )
    except (FileNotFoundError, FileExistsError, OSError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"frame_count": result["frame_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

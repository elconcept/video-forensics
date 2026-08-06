# Step 27: comparison views and perceptual provenance

This step replaces the single flattened view with three explicit views:

- `decoder` for native framemd5 runs
- `perceptual` for stored grayscale-frame runs
- `normalized` for normalized hash-only runs

It also adds the source SHA-256 to perceptual manifests and makes perceptual comparison reject runs that do not share one verified input hash.

Apply the perceptual correction once:

python3 perceptual.patch.py
rm perceptual.patch.py

Prepare views after verified bundle import:

python -m video_forensics.native.prepare_comparison_views results/1796_merged --output results/1796_views

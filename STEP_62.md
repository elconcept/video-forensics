# Step 62: one-command independent orphan decoding

This step adds `video-forensics-orphan-independent-run`.

One command now:

1. locates `dec265` or `de265dec`
2. locates FFmpeg
3. reads coded width and height from the Annex B SPS
4. builds every approved controlled stream
5. decodes every variant through libavcodec
6. decodes every variant independently through libde265
7. converts libde265 YUV frames to ordered lossless PNG
8. creates compatible decoder manifests
9. runs cross-decoder verification
10. runs recovery and the structured report

Example:

`video-forensics-orphan-independent-run results/source.h265 --plan results/orphan_plan_approved.json --output results/orphan_independent`

The command creates the complete result tree. No external decoder directory is prepared manually. Pixel format defaults to `yuv420p` and remains an explicit command parameter because coded dimensions alone do not identify the raw YUV layout.

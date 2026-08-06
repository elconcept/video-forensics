# Step 19: elementary HEVC stream and decoder diagnostics

This step adds the first codec-aware layer before pixel-domain interpretation:

- lossless HEVC Annex B extraction
- NAL boundary and header inventory
- IRAP and temporal-id checks
- single-thread and automatic-thread FFmpeg diagnostics
- explicit decoder-dependent status when missing-reference POC messages occur

The included parser deliberately does not claim full HEVC conformance analysis. SPS, PPS, slice-header, POC, RPS and CABAC parsing remain future work.

Apply CLI and pipeline integration once:

python3 cli.patch.py
rm cli.patch.py

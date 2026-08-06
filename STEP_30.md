# Step 30: orphan-tail recovery stability engine

This is the first implementation slice of `orphan_recovery`.

Input layout:

- one directory per controlled reference-picture variant
- matching decoded PNG or TIFF frame sequences in every directory

The module computes per frame:

- channel-wise median reconstruction
- per-pixel inter-variant standard deviation
- determined-pixel fraction
- a green overlay marking substitute-dependent pixels
- SHA-256 provenance for every supplied derivative frame

It does not yet build `[VPS+SPS+PPS][IDR_x][orphan slices]` streams. Stream construction and independent-decoder verification remain the next implementation slices.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py

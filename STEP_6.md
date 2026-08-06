# Step 6: streaming decoded-frame metrics

This stage decodes the first video stream directly from the source file through FFmpeg. It does not use previously exported PNG, WebP, or TIFF frames.

Metrics are calculated on a deterministic 480 x 270 grayscale stream:

- mean luminance
- luminance standard deviation
- mean absolute difference from the previous frame
- Laplacian variance
- grayscale entropy

The ranked inter-frame differences are candidates for later continuity analysis, not automatic findings of editing.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `frame_metrics/metrics.csv`
- `frame_metrics/findings.json`
- `frame_metrics/frame_metrics.json`

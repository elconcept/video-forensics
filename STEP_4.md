# Step 4: video timeline analysis

This stage uses FFprobe to preserve and normalize the first video stream timeline. It writes per-frame timestamps to CSV and reports mechanical timestamp anomalies without interpreting them as evidence of editing.

Outputs:

- `timeline/raw_ffprobe.json`
- `timeline/frames.csv`
- `timeline/anomalies.json`
- `timeline/timeline.json`

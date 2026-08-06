# Step 5: GOP and picture-type analysis

This stage independently obtains frame coding information from FFprobe and records:

- I/P/B picture sequence
- key-frame positions
- GOP boundaries and lengths
- packet bytes per GOP
- mechanical structural findings

It does not treat irregular GOP length as proof of editing.

## Applying the CLI integration

Run once after unpacking the overlay:

python3 cli.patch.py
rm cli.patch.py

## Outputs

- `gop/raw_ffprobe.json`
- `gop/frames.csv`
- `gop/gops.csv`
- `gop/findings.json`
- `gop/gop.json`

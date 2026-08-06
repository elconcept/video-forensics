# Step 11: audio packet analysis

This stage uses FFprobe to inspect the first audio stream. It preserves packet timestamps, durations, positions, sizes, and stream attributes.

It screens for:

- missing or non-monotonic packet timestamps
- packet timeline gaps or overlaps
- robust outliers in bytes per one-second window

It does not perform waveform, spectral, phase, ENF, splice, or crossfade authentication.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `audio/raw_ffprobe.json`
- `audio/packets.csv`
- `audio/windows.csv`
- `audio/findings.json`
- `audio/audio.json`

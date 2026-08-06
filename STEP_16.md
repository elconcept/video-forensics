# Step 16: pipeline profiles and dependency resolution

This stage separates the default analysis pipeline from optional operations and adds deterministic dependency expansion.

Default analysis excludes:

- `extract_frames`, because exporting every frame can consume substantial storage
- `reference_compare`, because it requires a separately prepared reference analysis

Examples:

- requesting `continuity` automatically schedules `timeline`, `gop`, and `frame_metrics` first
- requesting `compression` automatically schedules `gop` first
- requesting `av_sync` automatically schedules `timeline` and `audio` first
- requesting `reference_compare` requires `--reference-output`

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

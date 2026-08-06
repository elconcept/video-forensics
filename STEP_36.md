# Step 36: exact PCM zero-sample analysis

This step adds deterministic audio decoding to signed 16-bit PCM and reports:

- total scalar sample count
- audio frame count
- exact-zero scalar sample count and fraction
- sample rate and channel count
- decoded audio duration
- declared audio duration
- video duration
- video-minus-audio duration difference

The finding retains ordinary explanations such as silence, muting, padding, capture behavior, or processing. It does not convert a high zero-sample fraction into an authenticity conclusion.

If FFmpeg or FFprobe is unavailable, the module writes an `unavailable` manifest instead of aborting the wider run.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py

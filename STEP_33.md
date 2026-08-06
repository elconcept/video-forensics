# Step 33: decode controlled orphan variants

This step decodes every controlled stream emitted by `orphan_stream_builder` into lossless PNG frames.

It records for each variant:

- source stream SHA-256
- complete FFmpeg command
- return code and duration
- stdout and stderr
- frame count
- SHA-256 and size of every decoded PNG

The aggregate manifest states whether every run succeeded and whether all logs were free of missing-reference diagnostics. A failed or still-corrupt controlled stream is therefore not silently admitted to the stability engine.

The output layout is directly consumable by `video-forensics-orphan-recovery` because every stream receives its own variant subdirectory.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py

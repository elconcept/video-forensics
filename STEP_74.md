# Step 74: automatic reference comparison with FFmpeg trace_headers

This step executes the migration comparison on every HEVC input processed by the migration stage.

It runs FFmpeg with stream copy and the `trace_headers` bitstream filter, preserving the encoded payload while exposing header syntax for independent control. It then performs field-level comparison against normalized h265nal output and optional legacy output.

The acceptance manifest distinguishes:

- successful FFmpeg control
- whether legacy comparison was requested
- semantic agreement with legacy
- readiness for legacy removal

Legacy removal is never marked ready unless FFmpeg control succeeds and an explicitly supplied legacy result semantically agrees. FFmpeg documents that bitstream filters operate on encoded stream data without decoding and lists `trace_headers` among the available filters. citeturn135search304turn135search305turn135search308

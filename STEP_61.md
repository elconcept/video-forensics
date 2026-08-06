# Step 61: `verify_orphan_decoders`-compatible libde265 manifests

This step adds a canonical decoder-root manifest and one canonical manifest per controlled libde265 variant.

For each variant it writes:

- `decoder_manifest.json`
- `frames.csv`
- decoder and variant identifiers
- reference NAL number
- verified controlled-stream SHA-256
- frame directory
- contiguous decoder-output frame numbers
- PNG path, size, SHA-256
- source raw-frame index, offset, and SHA-256
- explicit ordering policy

At the decoder root it writes `manifest.json` with all variant identifiers, statuses, frame counts, frame directories, and per-variant manifest paths. The aggregate libde265 result points to this root manifest so `verify_orphan_decoders` can consume libde265 through the same decoder-root interface as the controlled libavcodec output.

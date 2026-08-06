# Step 59: h265nal integration with stable JSON

This step adopts `chemag/h265nal` as the primary HEVC syntax parser instead of continuing to duplicate VPS/SPS/PPS/RPS/slice syntax in Python.

It adds:

- a pinned build helper for h265nal
- cross-platform CMake build and local binary installation
- a Python adapter invoking the upstream Annex B CLI with offsets and lengths
- preservation of raw stdout and stderr
- conversion of the structured brace dump into versioned `h265nal.json`
- normalized per-NAL records with number, offset, length, header, parsed payload, and raw representation
- source SHA-256 and exact command provenance

The upstream project explicitly documents Annex B parsing, stateful VPS/SPS/PPS handling, slice parsing, offsets and lengths, unit tests, fuzzing, Windows support, and a BSD license. citeturn111search116turn112search129

The handwritten Python SPS/PPS parsers remain temporarily available as a legacy comparison backend. They should not be extended further before cross-validation against h265nal and FFmpeg.

# Step 69: stable C++ JSON envelope for h265nal

This step adds a cross-platform C++17 executable built with CMake. The wrapper invokes the pinned h265nal CLI with full-file Annex B parsing, offsets, lengths, and multiline output, then emits one stable JSON object containing:

- schema version
- backend identifier
- absolute input path
- command contract
- process status
- success flag
- complete stdout
- complete stderr

The bootstrap now builds both upstream h265nal and the JSON wrapper and records both binaries in `third_party/h265nal.lock.json`.

This is the transport-contract stage. Semantic normalization of h265nal output into the project schema remains the next migration task. The upstream tool documents full-file Annex B parsing and the `--add-length` and `--add-offset` CLI options. citeturn124search326

# Step 58: one human-readable Markdown summary per analyzed file

This step adds `video-forensics-result-summary`.

The command recursively reads JSON results produced under one file's output directory and creates exactly one `SUMMARY.md` at that directory's root. It consolidates:

- source path and SHA-256 when available
- module execution statuses
- unique structured findings ordered by severity
- observations and interpretation boundaries
- compact module metrics
- paths to the underlying manifests

The per-OS batch launchers invoke the summary after all automated analysis and packaging stages for each evidence file. Detailed JSON, CSV, logs, images, and hashes remain authoritative; `SUMMARY.md` is their human-readable index.

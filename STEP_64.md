# Step 64: automatic comparison across machines and timestamps

This step adds `video-forensics-cross-run-compare`.

For one stable source directory under `work/results/<file>/`, the module scans every direct child matching the UTC timestamp format and compares all available JSON results across runs. It records:

- all included timestamps
- source SHA-256 consistency
- module presence per run
- scalar status and count metrics
- structured finding identifiers
- modules whose collected results differ between runs

Outputs are written outside individual runs:

- `work/results/<file>/cross_run_comparison/comparison.json`
- `work/results/<file>/cross_run_comparison/COMPARISON.md`

All three per-OS launchers invoke the comparison after completing each file. Therefore a newly copied result from another machine is included automatically on the next run, and the command may also be executed directly against the file-level directory.

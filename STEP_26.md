# Step 26: flatten verified imported runs

The comparison tools expect one directory containing one child directory per decoder run. Verified imports retain a source-machine directory above each run.

This step creates a collision-free flattened view:

- `x1_intel__software_single_thread`
- `x1_intel__windows_intel_qsv`
- `pc_gtx960__software_single_thread`
- `pc_gtx960__windows_nvidia_cuda`

By default it creates directory symlinks and falls back to copying if symlinks are unavailable. Use `--copy` to force independent copies.

Example:

python -m video_forensics.native.flatten_imported_runs results/1796_merged --output results/1796_flat

The resulting directory can be passed directly to `compare_decoder_runs`.

# Step 53: one-command per-OS batch execution

This step adds one launcher per operating system. Every launcher processes all supported files placed directly in `work/evidence`, creates a UTC session under `work/results`, and runs baseline analysis, local decoder matrix, complete frame export, audio analysis, email-review packaging, and verified matrix packaging for each file.

`work/evidence` and `work/results` are tracked through `.gitkeep`; their contents are ignored. The X1 Carbon workflow is Windows-native for Quick Sync and D3D11VA. WSL is not used as the hardware-decoder execution path.

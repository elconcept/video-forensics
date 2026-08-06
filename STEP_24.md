# Step 24: unified Windows execution and result bundling

This step adds one PowerShell launcher for both Windows machines.

It runs, for every selected profile:

- the native framemd5 decoder run
- the perceptual normalized-frame run

After all profiles finish, it creates a ZIP bundle containing the complete result tree, an internal per-file manifest, and an external SHA-256 checksum file.

Intel machine:

powershell -ExecutionPolicy Bypass -File launchers/run_windows_matrix.ps1 -Platform intel -Video C:\evidence\1796.mp4 -Output C:\results\1796_intel

NVIDIA machine:

powershell -ExecutionPolicy Bypass -File launchers/run_windows_matrix.ps1 -Platform nvidia -Video C:\evidence\1796.mp4 -Output C:\results\1796_nvidia

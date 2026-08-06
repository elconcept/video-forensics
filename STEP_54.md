# Step 54: dependency bootstrap in every OS launcher

Each operating-system launcher now invokes a dedicated bootstrap before analysis.

- Linux and WSL use APT for Python, FFmpeg and optional analysis tools. Snap is only an FFmpeg fallback.
- macOS installs Homebrew when absent, then installs required and optional formulae.
- Windows uses winget first and Chocolatey as fallback.
- Required tools stop execution when installation or verification fails.
- Optional tools are attempted and logged but do not block the primary pipeline.
- Every bootstrap creates `.venv` when needed and reinstalls the editable project with development dependencies.

The Windows package identifiers include `Gyan.FFmpeg` and `OliverBetz.ExifTool`; Ubuntu uses the `ffmpeg`, `mediainfo`, and `libimage-exiftool-perl` packages; Homebrew formulae include `gpac` and `exiftool`. Package availability is still verified locally at execution time.

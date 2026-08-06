# Step 37: first-class local decoder matrix runner

This step promotes decoder-matrix execution to one cross-platform entry point.

It:

- captures the host profile once
- selects profiles for Linux, Windows, or macOS
- checks declared FFmpeg and device capabilities
- executes every locally supported profile
- records absent profiles and unavailable hardware paths without aborting the matrix
- preserves failed runs as explicit failures
- writes one matrix manifest linked to the host-profile identifier

New profiles cover Linux NVDEC, VAAPI, QSV, and macOS VideoToolbox. AVFoundation native and libde265 remain separate integrations because they are not FFmpeg hardware profiles.

Apply profiles and entry point once:

python3 profiles.patch.py
rm profiles.patch.py

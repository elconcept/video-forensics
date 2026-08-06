# video-forensics

`video-forensics` is a Python toolkit for reproducible examination of video files. It records technical observations, anomalies, decoder behavior, derived images, commands, tool versions, host capabilities, and input hashes.

The toolkit does **not** issue an automatic verdict that a recording is authentic or manipulated. Its outputs are intended for technical review and later evidentiary assessment.

## Core principles

- Input evidence is read-only.
- Outputs are written to a separate directory.
- Every relevant artefact is tied to an input SHA-256 value.
- Commands, parameters, versions, logs, and host information are preserved.
- Encoded-stream facts are distinguished from decoder-produced pixels.
- Missing-reference output is treated as decoder-dependent.
- Decoder disagreement is preserved as a diagnostic result.
- Extracted and reconstructed images are derivative analytical material.
- Missing optional tools produce `unavailable` results where supported instead of invalidating the entire analysis.

## Supported platforms

The package runs directly on bare hosts:

- Linux x86-64
- Windows 11 x86-64
- macOS arm64

Docker and Compose are not used. Native execution is required for access to actual GPU drivers and platform decode APIs.

## Main capabilities

### Baseline analysis

- SHA-256 and SHA-512 integrity hashes
- FFprobe, MediaInfo, and ExifTool metadata
- MP4/MOV container structure
- video and audio timelines
- GOP and frame-type analysis
- decoded-frame metrics
- continuity screening
- repeated-frame and repeated-sequence screening
- blending candidates
- compression-regime screening
- audio packet and exact PCM zero-sample analysis
- audio-video duration comparison
- consolidated report

### HEVC and decoder analysis

- HEVC extraction to Annex B
- NAL boundary and header inventory
- NAL type, layer, temporal identifier, and IRAP screening
- single-threaded and multi-threaded libavcodec diagnostics
- local hardware-decoder profile execution
- host capability collection
- decoder frame-count and frame-hash comparison
- normalized and perceptual cross-decoder comparison
- independent `dec265` / libde265 execution

### Orphaned-reference recovery

- byte-exact construction of controlled HEVC streams
- decoding controlled variants to lossless PNG
- per-pixel median reconstruction
- per-pixel inter-variant standard deviation
- determined and substitute-dependent pixel masks
- independent-decoder verification
- structured recovery finding without an authenticity verdict

### Human visual review

- export of all frames returned by selected decoders
- lossless full-resolution PNG tree
- compressed JPEG review tree for email submission
- per-frame SHA-256 indexes
- calibrated comparison of monitor recordings with extracted and recovered frames
- static connected-region screening during global frame change
- burned-in timestamp OCR
- OSD glyph geometry screening

## Current limitations

- The HEVC parser is not yet a complete conformance parser.
- Full SPS/PPS semantics, slice-header POC derivation, RPS graph construction, and CABAC inspection remain incomplete.
- AVFoundation native decoding requires a separate platform-specific implementation.
- Hardware support depends on the local FFmpeg build, GPU, driver, and operating system.
- OSD OCR requires visual confirmation.
- Glyph geometry does not identify a font.
- Pixel-domain modules remain decoder-dependent when concealment or missing references are present.
- PRNU, ENF, and complete waveform splice analysis are not implemented.

## Repository layout

```text
video-forensics/
├── .github/workflows/
├── docs/
├── launchers/
├── profiles/decoder_matrix/
├── scripts/
├── src/video_forensics/
│   ├── cli.py
│   ├── manifest.py
│   ├── pipeline.py
│   ├── process.py
│   ├── native/
│   └── tools/
├── tests/
├── pyproject.toml
└── README.md
```

# Installation

## 1. Python

Python 3.12 is recommended.

### Ubuntu or another Linux distribution

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

After changing dependencies or entry points, reinstall the editable package:

```bash
python -m pip install -e '.[dev]'
```

## 2. External tools

The toolkit discovers external binaries at runtime.

### Important tools

- `ffmpeg`
- `ffprobe`

### Optional tools

- `exiftool`
- `mediainfo`
- `mp4dump`
- `MP4Box`
- `dec265` or `de265dec`
- `tesseract`
- platform utilities such as `nvidia-smi`, `vainfo`, `lspci`, and `system_profiler`

Check installed paths:

```bash
command -v ffmpeg ffprobe exiftool mediainfo mp4dump MP4Box dec265 tesseract
```

On Windows:

```powershell
Get-Command ffmpeg, ffprobe, exiftool, mediainfo, MP4Box, dec265, tesseract -ErrorAction SilentlyContinue
```

## 3. Verify the installation

```bash
video-forensics --version
video-forensics tools
ruff check .
pytest
```

# Preparing an examination

Create separate evidence and result locations. Do not write into the evidence directory.

```bash
mkdir -p evidence results
cp /path/to/input.mp4 evidence/input.mp4
chmod a-w evidence/input.mp4
```

Record the source hash independently:

```bash
sha256sum evidence/input.mp4
```

On macOS:

```bash
shasum -a 256 evidence/input.mp4
```

On Windows PowerShell:

```powershell
Get-FileHash C:\evidence\input.mp4 -Algorithm SHA256
```

# Baseline pipeline

## Run the default analysis

```bash
video-forensics analyze evidence/input.mp4 --output results/input
```

The output directory must be separate from the evidence directory.

## List available stages

```bash
video-forensics tools
```

## Run selected stages

```bash
video-forensics analyze evidence/input.mp4 \
  --output results/input-selected \
  --stages integrity,metadata,timeline,gop,audio,av_sync,report
```

Stage dependencies are expanded automatically where configured.

## Compare with a reference analysis

First analyze the reference file:

```bash
video-forensics analyze evidence/reference.mp4 \
  --output results/reference
```

Then analyze the questioned file with the comparison stage:

```bash
video-forensics analyze evidence/questioned.mp4 \
  --output results/questioned \
  --stages reference_compare,report \
  --reference-output results/reference
```

# Host capability profile

Capture the host before hardware-decoder testing:

```bash
video-forensics-host-profile --output results/host_profile.json
```

The profile records:

- operating system and architecture
- Python executable and version
- CPU information
- GPU and driver probes
- availability and paths of external tools
- FFmpeg version and build configuration
- FFmpeg hardware accelerators and decoders
- a stable host profile identifier

Do not overwrite an existing profile. Write a new result directory for a new examination session.

# Local decoder matrix

The matrix runner selects profiles appropriate to the current operating system and records unsupported paths as `unavailable`.

```bash
video-forensics-run-matrix evidence/input.mp4 \
  --output results/input_matrix
```

Explicit FFmpeg paths may be supplied:

```bash
video-forensics-run-matrix evidence/input.mp4 \
  --output results/input_matrix \
  --ffmpeg /opt/ffmpeg/bin/ffmpeg \
  --ffprobe /opt/ffmpeg/bin/ffprobe
```

## Expected local profiles

### Linux

- software single-threaded
- software automatic-threaded
- CUDA/NVDEC when available
- VAAPI when available
- QSV when available

### Windows

- software single-threaded
- software automatic-threaded
- Intel QSV
- Intel D3D11VA
- NVIDIA D3D11VA
- NVIDIA CUDA/NVDEC

### macOS

- software single-threaded
- software automatic-threaded
- VideoToolbox through FFmpeg

A profile name does not prove that hardware decoding succeeded. Inspect:

- `matrix_manifest.json`
- each run's `manifest.json`
- `stderr.txt`
- return codes
- selected adapter information
- frame count

# Windows launchers

Run from the repository root.

## Intel host

```powershell
powershell -ExecutionPolicy Bypass -File launchers/run_windows_matrix.ps1 `
  -Platform intel `
  -Video C:\evidence\input.mp4 `
  -Output C:\results\input_intel `
  -Ffmpeg C:\ffmpeg\bin\ffmpeg.exe `
  -Ffprobe C:\ffmpeg\bin\ffprobe.exe
```

## NVIDIA host

```powershell
powershell -ExecutionPolicy Bypass -File launchers/run_windows_matrix.ps1 `
  -Platform nvidia `
  -Video C:\evidence\input.mp4 `
  -Output C:\results\input_nvidia `
  -Ffmpeg C:\ffmpeg\bin\ffmpeg.exe `
  -Ffprobe C:\ffmpeg\bin\ffprobe.exe
```

# Linux and macOS launchers

```bash
./launchers/run_linux_matrix.sh evidence/input.mp4 results/input_linux
```

```bash
./launchers/run_macos_matrix.sh evidence/input.mp4 results/input_macos
```

# Complete frame export for visual review

This command exports all frames returned by every selected decoder profile into one result tree.

```bash
video-forensics-export-visual-frames evidence/input.mp4 \
  --host-profile results/host_profile.json \
  --profile profiles/decoder_matrix/software_single_thread.json \
  --profile profiles/decoder_matrix/software_automatic_threads.json \
  --output results/visual_frames
```

Add hardware profiles supported by the host, for example:

```bash
video-forensics-export-visual-frames evidence/input.mp4 \
  --host-profile results/host_profile.json \
  --profile profiles/decoder_matrix/software_single_thread.json \
  --profile profiles/decoder_matrix/linux_nvdec.json \
  --output results/visual_frames
```

The output contains:

```text
visual_frames/
├── lossless/
│   └── <host_profile_id>__<decoder>/
│       ├── frame_000000001.png
│       ├── index.csv
│       └── stderr.txt
├── email/
│   └── <host_profile_id>__<decoder>/
│       ├── frame_000000001.jpg
│       ├── index.csv
│       └── stderr.txt
├── README_EMAIL_COPY.txt
└── visual_frame_export.json
```

## Meaning of the two trees

- `lossless`: full-resolution PNG derivatives for technical verification and human review.
- `email`: resized JPEG review copies intended for electronic submission.

The compressed tree contains a notice that lossless PNG derivatives are retained and can be supplied on request. The source recording remains the primary material.

Do not describe the JPEG files as lossless or as replacements for the source recording.

# Packaging and transfer of decoder results

## Build a verified bundle

```bash
python -m video_forensics.native.bundle_decoder_results \
  results/input_intel \
  --output results/input_intel.zip
```

This creates:

- a ZIP archive
- an internal file manifest
- an external `.sha256` file

Transfer both the ZIP and its `.sha256` file.

## Import a verified bundle

```bash
python -m video_forensics.native.import_decoder_bundles \
  results/input_intel.zip \
  --destination results/input_merged \
  --source-id x1_intel
```

Import another host under a different identifier:

```bash
python -m video_forensics.native.import_decoder_bundles \
  results/input_nvidia.zip \
  --destination results/input_merged \
  --source-id pc_gtx960
```

The importer verifies:

- external ZIP SHA-256
- archive path safety
- internal inventory
- size and SHA-256 of every declared file
- absence of unexpected files
- source-ID collision

# Preparing comparison views

```bash
python -m video_forensics.native.prepare_comparison_views \
  results/input_merged \
  --output results/input_views
```

This creates:

- `decoder/`
- `normalized/`
- `perceptual/`

Run directories receive source-host prefixes.

# Comparing decoder output

## Exact frame hashes and frame counts

```bash
python -m video_forensics.native.compare_decoder_runs \
  results/input_views/decoder \
  --output results/input_decoder_comparison
```

Outputs include:

- frame counts
- PTS values
- frame hashes
- first divergent frame
- missing-reference diagnostics

## Normalized frame-hash comparison

```bash
python -m video_forensics.native.compare_normalized_runs \
  results/input_views/normalized \
  --output results/input_normalized_comparison
```

## Perceptual comparison

```bash
python -m video_forensics.native.compare_perceptual_runs \
  results/input_views/perceptual \
  --output results/input_perceptual_comparison
```

Per frame, this records:

- MAE
- RMSE
- NCC
- identical-pixel fraction
- missing-frame status

# Exact audio sample analysis

```bash
video-forensics-audio-samples evidence/input.mp4 \
  --output results/audio_samples \
  --host-profile-id <host_profile_id>
```

The module reports:

- scalar PCM sample count
- audio frame count
- exact-zero sample count and fraction
- sample rate and channels
- decoded audio duration
- declared audio duration
- video-minus-audio duration difference

A high zero-sample fraction is an observation, not an authenticity verdict.

# HEVC elementary stream and orphan recovery

## 1. Obtain Annex B HEVC

Use the baseline `elementary_stream` stage or FFmpeg directly:

```bash
ffmpeg -nostdin -v error \
  -i evidence/input.mp4 \
  -map 0:v:0 -c:v copy \
  -bsf:v hevc_mp4toannexb \
  -f hevc results/input.h265
```

## 2. Prepare an explicit reconstruction plan

Example `plan.json`:

```json
{
  "parameter_nals": [1, 2, 3],
  "reference_idr_nals": [4, 55, 116, 147],
  "orphan_start_nal": 198,
  "orphan_end_nal": 241
}
```

The values above are only an example of the required schema. Use NAL numbers measured for the actual stream.

## 3. Build controlled streams

```bash
video-forensics-build-orphan-streams results/input.h265 \
  --plan plan.json \
  --output results/orphan_streams
```

For each selected IDR, the tool builds:

```text
[VPS/SPS/PPS][selected IDR][orphan NAL range]
```

## 4. Decode controlled streams

```bash
video-forensics-decode-orphan-variants results/orphan_streams \
  --output results/orphan_libavcodec \
  --decoder-id libavcodec \
  --decoder-arg=-threads \
  --decoder-arg=1
```

Review:

- `decode_orphan_variants.json`
- `all_successful`
- `all_logs_free_of_missing_reference`
- each variant's `stderr.txt`

Do not pass failed or still-corrupt variants into reconstruction.

## 5. Compute stability and reconstruction

```bash
video-forensics-orphan-recovery results/orphan_libavcodec \
  --output results/orphan_recovery \
  --sigma-threshold 8
```

Outputs include:

- median reconstructed frames
- green determination overlays
- per-frame determined-pixel fractions
- per-frame stability table
- source hashes for every derivative input frame

Green pixels in determination overlays remain dependent on the supplied reference substitute.

## 6. Run independent libde265 decoding

```bash
video-forensics-libde265-run results/input.h265 \
  --output results/libde265_full \
  --width 1920 \
  --height 1080 \
  --pixel-format yuv420p
```

Width, height, and pixel format are analyst-supplied because raw YUV is not self-describing. Confirm them against the stream parameters.

For controlled orphan variants, prepare an external decoder result tree with variant identifiers and manifests compatible with the verification tool.

## 7. Compare independent decoders

```bash
video-forensics-verify-orphan-decoders \
  --decoder-root results/orphan_libavcodec \
  --decoder-root results/orphan_libde265 \
  --output results/orphan_verification
```

## 8. Generate the structured recovery report

```bash
video-forensics-orphan-recovery-report \
  --recovery-root results/orphan_recovery \
  --verification-root results/orphan_verification \
  --host-profile results/host_profile.json \
  --output results/orphan_report
```

## 9. Orchestrated pipeline

```bash
video-forensics-orphan-pipeline results/input.h265 \
  --plan plan.json \
  --output results/orphan_pipeline \
  --external-decoder-root results/orphan_libde265 \
  --host-profile results/host_profile.json
```

Without an independent decoder result, reconstruction remains provisional and the verification/report stages remain pending.

# Playback-divergence analysis

Prepare:

- one monitor-recording frame with a known matching source frame
- the known source frame
- a directory of monitor-recording frames to test
- candidate directories such as `standard/` and `recovered/`

Example:

```bash
video-forensics-playback-divergence \
  --control-screen screen/control.png \
  --control-reference candidates/standard/frame_000000186.png \
  --screen-root screen/disputed \
  --candidates-root candidates \
  --output results/playback_divergence \
  --x-min 100 --x-max 400 \
  --y-min 100 --y-max 400 \
  --width-min 1200 --width-max 1700 \
  --step 2
```

The module:

1. searches crop position and scale on the control pair,
2. freezes that crop,
3. searches every supplied candidate frame,
4. reports the best and second-best NCC values and their margin.

Do not calibrate separately for disputed frames. Do not restrict candidates to a preferred temporal window.

# Static-region screening

Run on a sequence of decoded images:

```bash
video-forensics-static-region-motion \
  results/visual_frames/lossless/<host>__<decoder> \
  --output results/static_region_motion \
  --minimum-region-pixels 64 \
  --global-motion-threshold 2.0
```

A candidate requires both:

- global frame MAE above the configured threshold,
- at least one sufficiently large connected region of exactly identical grayscale pixels.

Review all candidates visually. Static overlays, masks, compression behavior, and genuinely motionless regions remain possible explanations.

# Burned-in timestamp OCR

Choose a fixed crop covering the timestamp in every frame.

```bash
video-forensics-osd-reader \
  results/visual_frames/lossless/<host>__<decoder> \
  --output results/osd_reader \
  --crop 20 1000 700 70 \
  --scale 4 \
  --language eng \
  --host-profile-id <host_profile_id>
```

The crop is expressed as:

```text
X Y WIDTH HEIGHT
```

Outputs include:

- raw OCR text
- parsed timestamp
- absent-reading ranges
- backwards timestamp movement
- commands and OCR diagnostics

Confirm every important OCR reading against the image.

# OSD glyph geometry

First create a directory containing timestamp-only crops with identical geometry.

```bash
video-forensics-osd-glyph-metrics osd_crops \
  --output results/osd_glyph_metrics \
  --threshold 180 \
  --minimum-pixels 3 \
  --baseline-tolerance 3 \
  --height-tolerance 5
```

This is a screening measurement. Findings require visual confirmation and device-reference material.

# Reading result status

Common statuses:

- `completed`: the module ran and wrote results.
- `failed`: execution was attempted but did not complete normally.
- `decoder_error`: the decoder returned an error.
- `unavailable`: a required optional tool or capability was absent.
- `not_applicable`: the input did not contain the relevant stream or feature.
- `pending`: a prerequisite such as independent verification is not yet supplied.

Do not silently discard failed or unavailable paths. They are part of the capability and decoder record.

# Validation before committing changes

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
pytest
python -m build
git diff --check
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m build
git diff --check
```

# Recommended examination workflow

1. Copy the source into a read-only evidence location.
2. Record SHA-256 independently.
3. Capture `host_profile.json`.
4. Run the baseline pipeline.
5. Run the local decoder matrix.
6. Export complete lossless and email-review frame trees.
7. Transfer and verify bundles from other hosts.
8. Compare frame counts, hashes, and perceptual output.
9. If missing references are present, inspect HEVC/NAL structure before interpreting pixels.
10. Run controlled orphan recovery only with an explicit measured NAL plan.
11. Obtain independent-decoder verification.
12. Use playback-divergence, OSD, and static-region modules only on clearly identified derivative frame sets.
13. Review every high-value finding visually and against raw logs.
14. Preserve all manifests, logs, CSV files, JSON files, and source hashes.

# Reporting language

Outputs should be described as observations, for example:

- “The decoder returned 192 frames.”
- “The stream produced 44 missing-reference diagnostics.”
- “The determined-pixel fraction reached 1.0 from the stated reconstructed frame onward.”
- “The two decoder outputs diverged at the stated frame.”

Avoid unsupported conclusions such as:

- “The file is authentic.”
- “The file was manipulated.”
- “The player revealed hidden frames.”
- “The recovered reference picture was identified.”

# License

No license has been declared. Add an explicit license before public distribution or accepting external contributions.

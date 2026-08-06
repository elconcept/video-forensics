# video-forensics

Reproducible toolkit for structural, codec-aware, decoder-matrix, audio, timeline, and pixel-domain examination of video files.

The project has two execution modes:

1. **Container pipeline on Linux** for repeatable baseline analysis.
2. **Native Python decoder matrix** for Windows hardware decoders such as Intel QSV, D3D11VA, and NVIDIA CUDA/NVDEC.

The tools record observations and decoder behavior. They do not automatically issue an authenticity verdict.

## Current scope

### Container pipeline

The default pipeline includes:

- input identity, SHA-256, and SHA-512
- FFprobe, MediaInfo, and ExifTool metadata
- ISO BMFF / MP4 / MOV atom inventory
- HEVC Annex B extraction and NAL-header inventory
- single-thread and automatic-thread decoder diagnostics
- video PTS, DTS, and duration analysis
- GOP and I/P/B frame analysis
- decoded-frame metrics
- continuity correlation
- duplicate-frame and repeated-sequence screening
- linear-blending candidates
- packet-size compression-regime screening
- audio packet timeline analysis
- audio-video alignment
- consolidated Markdown report

Optional stages:

- lossless frame extraction
- comparison with a separately analyzed reference recording

### Native decoder matrix

The native workflow supports profiles for:

- software decoding with one thread
- software decoding with automatic threading
- Intel QSV on Windows
- Intel D3D11VA on Windows
- NVIDIA D3D11VA on Windows
- NVIDIA CUDA/NVDEC on Windows

Each run preserves the command, environment inventory, input hash, FFmpeg logs, frame count, and frame checksums. Perceptual runs additionally preserve normalized grayscale derivative frames for MAE, RMSE, NCC, and identical-pixel comparison.

## Important interpretation rule

Pixel-domain output is decoder-dependent when the encoded stream contains missing or invalid references. The project therefore performs codec and decoder diagnostics before interpreting decoded-frame metrics.

The current HEVC parser inventories Annex B NAL boundaries and headers, NAL types, IRAP presence, layer identifiers, and temporal identifiers. It does **not yet** derive full SPS/PPS semantics, slice-header POC, RPS dependency graphs, or CABAC syntax.

## Repository layout

```text
video-forensics/
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── profiles/decoder_matrix/
├── launchers/
├── scripts/
├── src/video_forensics/
│   ├── cli.py
│   ├── pipeline.py
│   ├── native/
│   └── tools/
├── tests/
└── docs/
```

## Linux container workflow

### Build

```bash
docker build -t video-forensics:local .
```

### Prepare directories

```bash
mkdir -p evidence results
cp /path/to/input.mp4 evidence/
```

### Run the default pipeline

```bash
EVIDENCE_DIR="$PWD/evidence" RESULTS_DIR="$PWD/results" \
  docker compose run --rm forensic analyze \
  /evidence/input.mp4 --output /results/input
```

The evidence directory is mounted read-only. Results are written separately.

### Run selected stages

Dependencies are expanded automatically. For example, requesting `continuity` also schedules `timeline`, `gop`, and `frame_metrics`.

```bash
EVIDENCE_DIR="$PWD/evidence" RESULTS_DIR="$PWD/results" \
  docker compose run --rm forensic analyze \
  /evidence/input.mp4 --output /results/input \
  --stages continuity,compression,report
```

### Optional frame extraction

```bash
EVIDENCE_DIR="$PWD/evidence" RESULTS_DIR="$PWD/results" \
  docker compose run --rm forensic analyze \
  /evidence/input.mp4 --output /results/input_frames \
  --stages integrity,extract_frames,report
```

### Reference-output comparison

Analyze the reference recording first, then pass its output directory:

```bash
video-forensics analyze questioned.mp4 \
  --output results/questioned \
  --stages reference_compare,report \
  --reference-output results/reference
```

## Native Python setup

Python 3.12 is used by the project.

### Linux or macOS development environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

### Windows PowerShell environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

FFmpeg and FFprobe must either be available through `PATH` or passed explicitly to the launchers.

## Windows decoder matrix

Run commands from the repository root.

### Intel machine

```powershell
powershell -ExecutionPolicy Bypass -File launchers/run_windows_matrix.ps1 `
  -Platform intel `
  -Video C:\evidence\input.mp4 `
  -Output C:\results\input_intel `
  -Ffmpeg C:\ffmpeg\bin\ffmpeg.exe `
  -Ffprobe C:\ffmpeg\bin\ffprobe.exe
```

This requests software single-thread, software automatic-thread, Intel QSV, and Intel D3D11VA profiles.

### NVIDIA machine

```powershell
powershell -ExecutionPolicy Bypass -File launchers/run_windows_matrix.ps1 `
  -Platform nvidia `
  -Video C:\evidence\input.mp4 `
  -Output C:\results\input_nvidia `
  -Ffmpeg C:\ffmpeg\bin\ffmpeg.exe `
  -Ffprobe C:\ffmpeg\bin\ffprobe.exe
```

This requests software single-thread, software automatic-thread, NVIDIA D3D11VA, and NVIDIA CUDA/NVDEC profiles.

A requested hardware backend can fail because of the FFmpeg build, driver, device capability, or adapter selection. Review each `manifest.json` and `stderr.txt`; do not infer successful hardware use from the profile name alone.

## Result bundles

The Windows launcher creates a ZIP bundle, an internal per-file manifest, and an external SHA-256 file.

### Import verified bundles

```bash
python -m video_forensics.native.import_decoder_bundles \
  input_intel.zip \
  --destination results/input_merged \
  --source-id x1_intel

python -m video_forensics.native.import_decoder_bundles \
  input_nvidia.zip \
  --destination results/input_merged \
  --source-id pc_gtx960
```

The importer verifies the external ZIP checksum, safe archive paths, the internal file inventory, file sizes, and per-file SHA-256 values.

### Prepare comparison views

```bash
python -m video_forensics.native.prepare_comparison_views \
  results/input_merged \
  --output results/input_views
```

This creates separate `decoder`, `perceptual`, and `normalized` views with source-machine prefixes.

### Compare native decoder runs

```bash
python -m video_forensics.native.compare_decoder_runs \
  results/input_views/decoder \
  --output results/input_decoder_comparison
```

### Compare normalized hashes

```bash
python -m video_forensics.native.compare_normalized_runs \
  results/input_views/normalized \
  --output results/input_normalized_comparison
```

### Compare perceptual outputs

```bash
python -m video_forensics.native.compare_perceptual_runs \
  results/input_views/perceptual \
  --output results/input_perceptual_comparison
```

Comparison tools reject runs whose recorded source SHA-256 values do not agree where that verification is required.

## Principal outputs

```text
results/input/
├── manifest.json
├── report.md
├── integrity/
├── metadata/
├── container/
├── elementary_stream/
├── hevc_bitstream/
├── decoder_diagnostics/
├── timeline/
├── gop/
├── frame_metrics/
├── continuity/
├── duplicates/
├── blending/
├── compression/
├── audio/
└── av_sync/
```

## Validation

```bash
source .venv/bin/activate
ruff check .
pytest
python -m build
./scripts/container_smoke_test.sh
```

## Forensic handling principles

- Never modify the input recording.
- Preserve and verify the source hash before interpretation.
- Keep evidence and output directories separate.
- Preserve raw tool output, exact commands, versions, and logs.
- Distinguish encoded-stream facts from decoder-produced pixels.
- Treat missing-reference output as decoder-dependent.
- Compare only runs tied to the same verified input hash.
- Treat extracted and normalized frames as derivative analytical material.
- Interpret anomalies jointly; a single metric is not proof of editing.

## Known limitations

- The HEVC parser is not yet a complete conformance parser.
- Hardware profiles require compatible FFmpeg builds, drivers, and devices.
- Hardware frame download and pixel-format conversion can differ by backend.
- Packet-size, blending, duplicate, and pixel-metric modules are screening tools.
- PRNU, ENF, full waveform splice analysis, CABAC inspection, and complete HEVC RPS/POC derivation are not yet implemented.

## License

No license has been declared yet. Add an explicit license before distributing or accepting external contributions.

# Step 2: independent metadata extraction

This stage runs FFprobe, MediaInfo, and ExifTool independently. It preserves each raw JSON result, records exact commands and version output, and writes a small normalized summary.

## Local validation

```bash
source .venv/bin/activate
ruff check .
pytest
```

## Container smoke test

```bash
docker build -t video-forensics:step2 .
docker run --rm --network none --read-only \
  --tmpfs /tmp:size=2g \
  -v "$PWD/evidence:/evidence:ro" \
  -v "$PWD/results:/results:rw" \
  video-forensics:step2 analyze /evidence/test.mov --output /results/test
```

Expected new outputs:

```text
results/test/metadata/metadata.json
results/test/metadata/raw/ffprobe.json
results/test/metadata/raw/mediainfo.json
results/test/metadata/raw/exiftool.json
```

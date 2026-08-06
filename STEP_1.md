# Step 1: integrity and execution manifest

Copy the included files over the repository root, then run:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
ruff check .
pytest
```

Container smoke test:

```bash
docker build -t video-forensics:step1 .
mkdir -p evidence results
cp /path/to/test.mov evidence/
docker run --rm --network none --read-only \
  --tmpfs /tmp:size=2g \
  -v "$PWD/evidence:/evidence:ro" \
  -v "$PWD/results:/results:rw" \
  video-forensics:step1 analyze /evidence/test.mov --output /results/test
```

Expected outputs:

```text
results/test/manifest.json
results/test/integrity/hashes.json
```

# Step 3: ISO BMFF container structure

This stage parses MP4/MOV-family atom headers without modifying or decoding the input. It records offsets, sizes, nesting, top-level order, atom counts, and structural boundary anomalies.

## Validation

```bash
source .venv/bin/activate
ruff check .
pytest
```

## Run only this stage

```bash
docker compose run --rm forensic analyze /evidence/test.mov \
  --output /results/test \
  --stages container_structure
```

Expected output:

```text
results/test/container/structure.json
```

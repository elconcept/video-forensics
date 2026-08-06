# video-forensics

Reproducible, containerized toolkit for forensic examination of video files.

Status: repository scaffold. Analytical modules are intentionally not implemented yet.

## Principles

- input evidence is mounted read-only
- outputs are written to a separate directory
- every run records tool versions, parameters, logs, and hashes
- modules produce observations and anomalies, not an automatic authenticity verdict
- each analytical tool remains independently executable

## Planned command

```bash
docker compose run --rm forensic analyze /evidence/input.mov --output /results/input
```

## Repository layout

- `src/video_forensics/cli.py` - orchestrator CLI
- `src/video_forensics/tools/` - one analysis tool per file
- `tests/` - automated tests
- `docs/` - method and validation documentation
- `.github/workflows/` - CI and container build

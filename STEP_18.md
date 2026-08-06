# Step 18: CI and package validation

This step strengthens GitHub Actions so every push and pull request performs:

- Ruff validation
- the complete pytest suite
- Python package build
- Docker image build
- application version check inside the image
- the container smoke test

It also verifies that the installed package version matches `video_forensics.__version__`.

Apply the dependency update once:

python3 pyproject.patch.py
rm pyproject.patch.py

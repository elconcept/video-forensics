# Step 17: pipeline finalization and container smoke test

This step fixes report ordering so that `report.md` reads a manifest already marked as completed. The final manifest is then written again with the report stage result.

It also adds a container-level smoke test that:

- builds the image
- generates a short synthetic MP4 with video and audio inside the container
- runs the default pipeline with networking disabled and the root filesystem read-only
- verifies the principal output files and completed manifest

Apply the CLI correction once:

python3 cli.patch.py
rm cli.patch.py

Run the container smoke test separately after unit tests:

./scripts/container_smoke_test.sh

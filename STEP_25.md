# Step 25: verified bundle import

This step verifies and imports result bundles copied from the Windows machines.

Validation order:

- external ZIP SHA-256
- safe ZIP member paths
- internal bundle manifest
- size and SHA-256 of every declared file
- exact agreement between declared and present files
- collision-free source identifier

Example imports:

python -m video_forensics.native.import_decoder_bundles 1796_intel.zip --destination results/1796_merged --source-id x1_intel

python -m video_forensics.native.import_decoder_bundles 1796_nvidia.zip --destination results/1796_merged --source-id pc_gtx960

After import, native comparison tools can consume the verified merged result tree.

# Step 14: reference-analysis comparison

This stage compares an existing analysis output for the questioned recording with an existing analysis output for a reference recording.

It compares selected:

- FFprobe video and format attributes
- ISO BMFF top-level order and atom counts
- GOP summary properties

It does not establish device identity, perform PRNU analysis, or prove common origin.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Run with:

video-forensics analyze /evidence/questioned.mov --output /results/questioned --reference-output /results/reference

Outputs:

- `reference_compare/comparisons.json`
- `reference_compare/differences.json`
- `reference_compare/reference_compare.json`

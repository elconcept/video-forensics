# Step 35: structured orphan-recovery finding

This step combines the stability output and independent-decoder verification into one structured finding record.

The record follows the project reporting contract:

- id
- severity
- description
- evidence references
- requires-reference flag
- host-profile identifier
- measured observations
- retained mundane technical explanation
- interpretation boundary

It also writes a concise Markdown report without an authenticity verdict.

Apply the entry point once:

python3 pyproject.patch.py
rm pyproject.patch.py

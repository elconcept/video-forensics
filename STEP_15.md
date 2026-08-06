# Step 15: consolidated factual report

This stage creates a Markdown inventory of the analysis run. It records input identity, integrity hashes, stage status, and counts of observation records found in expected output files.

The report intentionally does not calculate an authenticity score or issue an automatic modified/not-modified verdict.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `report.md`
- `report.json`

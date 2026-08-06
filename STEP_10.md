# Step 10: compression-regime screening

This stage consumes packet sizes and picture types previously preserved by the GOP stage. It groups frames into fixed windows and reports robust outliers in window packet-size medians.

This is a screening layer only. It does not inspect macroblock quantization, motion vectors, coding-tree units, or prove double compression.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `compression/windows.csv`
- `compression/findings.json`
- `compression/compression.json`

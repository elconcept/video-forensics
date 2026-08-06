# Step 9: linear blending candidates

This stage tests each interior frame against a linear combination of its immediate neighbors. It records the fitted alpha, residual, baseline error, residual ratio, and differences from both neighbors.

A candidate indicates that a frame is unusually well approximated by its neighbors. It is not by itself proof of a cross-dissolve, interpolation, or editing operation.

Apply CLI integration once:

python3 cli.patch.py
rm cli.patch.py

Outputs:

- `blending/metrics.csv`
- `blending/findings.json`
- `blending/blending.json`

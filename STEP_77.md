# Step 77: enroll verified real reference results

This step removes manual placeholders from the reference-regression workflow.

The enrollment command accepts a real source file and its completed `reference_comparison.json`. Before adding the case, it requires:

- successful FFmpeg control
- explicit legacy comparison
- the configured minimum number of comparable records
- complete RPS coverage unless explicitly relaxed

It computes the source SHA-256 itself, rejects duplicate case identifiers, records the observed comparison evidence, and writes a directly executable regression configuration. A synthetic or incomplete comparison cannot be enrolled as migration evidence.
